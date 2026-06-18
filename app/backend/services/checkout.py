from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from app.backend.services.pricing import earned_points_for_amount
from app.backend.services.push_notifications import send_order_status_push


class CheckoutConflictError(RuntimeError):
    pass


class PaymentValidationError(RuntimeError):
    pass


def validate_authorized_transaction(payment: dict, transaction: dict) -> None:
    status = str(transaction.get("status", "")).upper()
    if status != "AUTHORIZED":
        raise PaymentValidationError(f"Transacción no autorizada: {status or 'SIN ESTADO'}")

    expected_amount = int(payment.get("total", payment.get("amount", 0)))
    confirmed_amount = int(transaction.get("amount") or 0)
    if confirmed_amount != expected_amount:
        raise PaymentValidationError(
            f"El monto confirmado ({confirmed_amount}) no coincide con el esperado ({expected_amount})"
        )

    expected_order = str(payment.get("buy_order", ""))
    confirmed_order = str(transaction.get("buy_order", ""))
    if expected_order and confirmed_order != expected_order:
        raise PaymentValidationError("La orden confirmada por Webpay no coincide con el pago")


async def reserve_stock(database, items: list[dict]) -> list[dict]:
    reserved: list[dict] = []
    for item in items:
        product_id = ObjectId(item["product_id"])
        quantity = int(item.get("quantity", 0))
        result = await database.products.update_one(
            {"_id": product_id, "stock": {"$gte": quantity}},
            {"$inc": {"stock": -quantity}},
        )
        if result.modified_count != 1:
            await release_stock(database, reserved)
            raise CheckoutConflictError(
                f"Stock insuficiente para {item.get('name', 'un producto')}. "
                "El pedido no fue creado y requiere revisión del pago."
            )
        reserved.append({"product_id": product_id, "quantity": quantity})
    return reserved


async def release_stock(database, reserved: list[dict]) -> None:
    for item in reserved:
        await database.products.update_one(
            {"_id": item["product_id"]},
            {"$inc": {"stock": int(item["quantity"])}},
        )


def user_preference_increments(items: list[dict]) -> dict[str, int]:
    increments: dict[str, int] = {}
    for item in items:
        category = str(item.get("category", "General"))
        key = f"preferences.{category}"
        increments[key] = increments.get(key, 0) + int(item.get("quantity", 1))
    return increments


async def create_order_after_authorization(database, payment: dict, transaction: dict) -> dict:
    """Crea exactamente un pedido y descuenta stock de forma condicional.

    El pago se reclama con un update atómico. Cada descuento usa `stock >= cantidad`,
    por lo que dos confirmaciones concurrentes no pueden dejar stock negativo.
    """

    validate_authorized_transaction(payment, transaction)

    existing_order = await database.orders.find_one({"webpay_token": payment["token"]})
    if existing_order is not None:
        return existing_order

    payment_filter = {"token": payment["token"]}
    if payment.get("_id") is not None:
        payment_filter = {"_id": payment["_id"]}
    payment_filter.update(
        {
            "order_created": {"$ne": True},
            "processing_order": {"$ne": True},
        }
    )

    claim = await database.payments.update_one(
        payment_filter,
        {
            "$set": {
                "processing_order": True,
                "processing_started_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    if claim.modified_count != 1:
        existing_order = await database.orders.find_one({"webpay_token": payment["token"]})
        if existing_order is not None:
            return existing_order
        raise CheckoutConflictError("Este pago ya está siendo procesado")

    reserved: list[dict] = []
    order_id = None
    user_adjusted = False
    points_earned = earned_points_for_amount(int(payment.get("product_amount_paid", 0)))
    points_to_spend = int(payment.get("points_to_spend", 0))
    points_delta = points_earned - points_to_spend
    preference_increments = user_preference_increments(payment.get("items", []))
    user_increments = {"points": points_delta, **preference_increments}

    try:
        user = await database.users.find_one({"_id": ObjectId(payment["user_id"])})
        if user is None:
            raise CheckoutConflictError("El usuario asociado al pago ya no existe")
        if int(user.get("points", 0)) < points_to_spend:
            raise CheckoutConflictError("El saldo de puntos cambió antes de confirmar el pago")

        reserved = await reserve_stock(database, payment.get("items", []))

        user_update = await database.users.update_one(
            {"_id": user["_id"], "points": {"$gte": points_to_spend}},
            {"$inc": user_increments},
        )
        if user_update.modified_count != 1:
            raise CheckoutConflictError("No fue posible actualizar los puntos del usuario")
        user_adjusted = True

        order = {
            "user_id": payment["user_id"],
            "user_email": user.get("email", ""),
            "user_name": user.get("name", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "items": payment.get("items", []),
            "shipping_address": payment.get("shipping_address", {}),
            "shipping_address_text": payment.get("shipping_address_text", ""),
            "subtotal": int(payment.get("subtotal", 0)),
            "shipping": int(payment.get("shipping", 0)),
            "discount": int(payment.get("discount", 0)),
            "total": int(payment.get("total", 0)),
            "status": "Pagado",
            "status_history": [],
            "payment_status": "paid",
            "buy_order": payment.get("buy_order", ""),
            "webpay_token": payment["token"],
            "authorization_code": transaction.get("authorization_code"),
            "points_earned": points_earned,
        }
        insertion = await database.orders.insert_one(order)
        order_id = insertion.inserted_id
        order["_id"] = order_id

        payment_update = await database.payments.update_one(
            {"token": payment["token"]},
            {
                "$set": {
                    "order_id": str(order_id),
                    "order_created": True,
                    "processing_order": False,
                    "fulfillment_error": "",
                }
            },
        )
        if payment_update.matched_count != 1:
            raise CheckoutConflictError("No fue posible asociar el pedido con el pago")

    except Exception as exc:
        if order_id is not None:
            await database.orders.delete_one({"_id": order_id})
        if user_adjusted:
            await database.users.update_one(
                {"_id": ObjectId(payment["user_id"])},
                {"$inc": {key: -value for key, value in user_increments.items()}},
            )
        if reserved:
            await release_stock(database, reserved)
        await database.payments.update_one(
            {"token": payment["token"]},
            {
                "$set": {
                    "processing_order": False,
                    "fulfillment_error": str(exc),
                    "requires_manual_review": True,
                }
            },
        )
        raise

    await send_order_status_push(order, "Pagado")
    return order
