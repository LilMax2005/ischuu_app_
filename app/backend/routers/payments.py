from __future__ import annotations

import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.backend.core.config import settings
from app.backend.core.security import decode_token
from app.backend.db import db
from app.backend.services.pricing import calculate_cart_totals, earned_points_for_amount
from app.backend.services.transbank import create_webpay_transaction, commit_transaction

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    return await decode_token(authorization.replace("Bearer ", "").strip())


async def enrich_cart_items(items: list[dict]) -> list[dict]:
    if not items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    enriched_items = []

    for item in items:
        product_id = item.get("product_id")
        quantity = int(item.get("quantity", 1))

        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Cantidad inválida")

        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except Exception as exc:
            raise HTTPException(status_code=400, detail="ID de producto inválido") from exc

        if product is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        stock = int(product.get("stock", 0))
        if stock < quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {product['name']}")

        price = int(product.get("price", 0))
        subtotal = price * quantity

        enriched_items.append(
            {
                "product_id": str(product["_id"]),
                "name": product["name"],
                "category": product.get("category", "General"),
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    return enriched_items


@router.post("/webpay/quote")
async def quote_cart_payment(payload: dict, user: dict = Depends(current_user)):
    enriched_items = await enrich_cart_items(payload.get("items", []))
    totals = calculate_cart_totals(
        enriched_items,
        user,
        use_points=bool(payload.get("use_points", False)),
        requested_points=payload.get("requested_points"),
    )
    return {"items": enriched_items, **totals}


@router.post("/webpay/cart")
async def create_cart_payment(payload: dict, user: dict = Depends(current_user)):
    enriched_items = await enrich_cart_items(payload.get("items", []))
    totals = calculate_cart_totals(
        enriched_items,
        user,
        use_points=bool(payload.get("use_points", False)),
        requested_points=payload.get("requested_points"),
    )

    if int(totals["total"]) <= 0:
        raise HTTPException(status_code=400, detail="Total inválido")

    buy_order = f"ISCHUU-{uuid.uuid4().hex[:10].upper()}"
    return_url = f"{settings.api_base_url}/api/v1/payments/webpay/return"

    try:
        response = create_webpay_transaction(
            buy_order=buy_order,
            session_id=str(user["_id"]),
            amount=int(totals["total"]),
            return_url=return_url,
        )

        await db.payments.insert_one(
            {
                "user_id": str(user["_id"]),
                "buy_order": buy_order,
                "items": enriched_items,
                "subtotal": totals["subtotal"],
                "shipping": totals["shipping"],
                "discount": totals["total_discount"],
                "preference_discount": totals["preference_discount"],
                "points_discount": totals["points_discount"],
                "points_to_spend": totals["points_to_spend"],
                "points_discount_label": totals["points_discount_label"],
                "points_earned_estimated": totals["points_earned_estimated"],
                "product_amount_paid": totals["product_amount_paid"],
                "total": totals["total"],
                "amount": totals["total"],
                "status": "created",
                "token": response["token"],
                "order_created": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return {
            "buy_order": buy_order,
            "amount": totals["total"],
            "token": response["token"],
            "url": response["url"],
            "redirect_url": response["redirect_url"],
            **totals,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo iniciar Webpay: {exc}") from exc


@router.post("/webpay/commit")
async def commit_payment(payload: dict):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token requerido")
    tx = commit_transaction(token)
    return await finalize_payment(token, tx)


@router.api_route("/webpay/return", methods=["GET", "POST"], response_class=HTMLResponse)
async def webpay_return(request: Request):
    data = dict(request.query_params)
    if request.method == "POST":
        form = await request.form()
        data.update(dict(form))

    token = data.get("token_ws")
    if not token:
        return HTMLResponse("<h2>Pago cancelado</h2><p>No se recibió token_ws.</p>")

    try:
        tx = commit_transaction(token)
        result = await finalize_payment(token, tx)
    except Exception as exc:
        return HTMLResponse(f"<h2>Error al confirmar pago</h2><p>{exc}</p>")

    return HTMLResponse(
        f"""
        <html>
            <body style="font-family: Arial; padding: 30px;">
                <h2>Resultado del pago Ischuu</h2>
                <p><b>Estado:</b> {result.get('status')}</p>
                <p><b>Total:</b> ${result.get('total', 0)}</p>
                <p><b>Puntos ganados:</b> {result.get('points_earned', 0)}</p>
                <p>Ya puedes volver a la aplicación y presionar Verificar pago.</p>
            </body>
        </html>
        """
    )


async def finalize_payment(token: str, tx: dict) -> dict:
    payment = await db.payments.find_one({"token": token})
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    status = str(tx.get("status", "")).upper()
    amount = int(tx.get("amount") or 0)

    await db.payments.update_one(
        {"token": token},
        {
            "$set": {
                "status": status,
                "amount_confirmed": amount,
                "transaction": tx,
                "committed_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    if status != "AUTHORIZED":
        return {"status": status, "total": payment.get("total", 0), "points_earned": 0}

    existing_order = await db.orders.find_one({"webpay_token": token})
    if existing_order:
        return {
            "status": "AUTHORIZED",
            "order_id": str(existing_order["_id"]),
            "total": existing_order.get("total", 0),
            "points_earned": existing_order.get("points_earned", 0),
        }

    points_earned = earned_points_for_amount(int(payment.get("product_amount_paid", 0)))
    points_to_spend = int(payment.get("points_to_spend", 0))
    points_balance_change = points_earned - points_to_spend

    order = {
        "user_id": payment["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "items": payment["items"],
        "subtotal": payment.get("subtotal", 0),
        "shipping": payment.get("shipping", 0),
        "discount": payment.get("discount", 0),
        "preference_discount": payment.get("preference_discount", 0),
        "points_discount": payment.get("points_discount", 0),
        "points_used": points_to_spend,
        "points_discount_label": payment.get("points_discount_label", ""),
        "product_amount_paid": int(payment.get("product_amount_paid", 0)),
        "total": payment.get("total", 0),
        "status": "Pagado",
        "payment_status": "paid",
        "buy_order": payment.get("buy_order"),
        "webpay_token": token,
        "authorization_code": tx.get("authorization_code"),
        "points_earned": points_earned,
    }

    result = await db.orders.insert_one(order)

    preferences_inc = {}
    for item in payment.get("items", []):
        category = item.get("category", "General")
        preferences_inc[f"preferences.{category}"] = preferences_inc.get(f"preferences.{category}", 0) + int(item.get("quantity", 1))

        await db.products.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -int(item.get("quantity", 1))}},
        )

    await db.users.update_one(
        {"_id": ObjectId(payment["user_id"])},
        {"$inc": {"points": points_balance_change, **preferences_inc}},
    )

    await db.payments.update_one(
        {"token": token},
        {"$set": {"order_id": str(result.inserted_id), "order_created": True}},
    )

    return {
        "status": "AUTHORIZED",
        "order_id": str(result.inserted_id),
        "total": payment.get("total", 0),
        "points_earned": points_earned,
    }


@router.get("/webpay/status/{token}")
async def get_payment_status(token: str, user: dict = Depends(current_user)):
    payment = await db.payments.find_one({"token": token})

    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if payment.get("user_id") != str(user["_id"]) and not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="No autorizado")

    return {
        "token": token,
        "status": payment.get("status", "created"),
        "order_created": bool(payment.get("order_created", False)),
        "order_id": payment.get("order_id"),
        "amount": int(payment.get("amount", 0)),
        "total": int(payment.get("total", 0)),
    }
