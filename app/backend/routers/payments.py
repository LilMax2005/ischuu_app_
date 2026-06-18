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
from app.backend.services.push_notifications import send_order_status_push
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

def normalize_shipping_address(data: dict) -> dict:
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Dirección de despacho requerida",
        )

    recipient = str(data.get("recipient", "")).strip()
    phone = str(data.get("phone", "")).strip()
    region = str(data.get("region", "")).strip()
    comuna = str(data.get("comuna", "")).strip()
    street = str(data.get("street", "")).strip()
    number = str(data.get("number", "")).strip()
    details = str(data.get("details", "")).strip()

    required_fields = {
        "Nombre destinatario": recipient,
        "Teléfono": phone,
        "Región": region,
        "Comuna": comuna,
        "Calle": street,
        "Número": number,
    }

    missing = [
        field_name
        for field_name, value in required_fields.items()
        if not value
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan datos de despacho: {', '.join(missing)}",
        )

    full_address = f"{street} {number}, {comuna}, {region}"

    if details:
        full_address = f"{full_address}. Referencia: {details}"

    return {
        "recipient": recipient,
        "phone": phone,
        "region": region,
        "comuna": comuna,
        "street": street,
        "number": number,
        "details": details,
        "full_address": full_address,
    }

def normalize_shipping_address(data: dict) -> dict:
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Dirección de despacho requerida",
        )

    recipient = str(data.get("recipient", "")).strip()
    phone = str(data.get("phone", "")).strip()
    region = str(data.get("region", "")).strip()
    comuna = str(data.get("comuna", "")).strip()
    street = str(data.get("street", "")).strip()
    number = str(data.get("number", "")).strip()
    details = str(data.get("details", "")).strip()

    required_fields = {
        "Nombre destinatario": recipient,
        "Teléfono": phone,
        "Región": region,
        "Comuna": comuna,
        "Calle": street,
        "Número": number,
    }

    missing = [
        field_name
        for field_name, value in required_fields.items()
        if not value
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan datos de despacho: {', '.join(missing)}",
        )

    full_address = f"{street} {number}, {comuna}, {region}"

    if details:
        full_address = f"{full_address}. Referencia: {details}"

    return {
        "recipient": recipient,
        "phone": phone,
        "region": region,
        "comuna": comuna,
        "street": street,
        "number": number,
        "details": details,
        "full_address": full_address,
    }

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
    shipping_address = normalize_shipping_address(
        payload.get("shipping_address", {})
    )
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

                "shipping_address": shipping_address,
                "shipping_address_text": shipping_address.get("full_address", ""),

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
                "webpay_url": response.get("url"),
                "order_created": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        redirect_url = f"{settings.api_base_url}/api/v1/payments/webpay/redirect/{response['token']}"

        return {
            "buy_order": buy_order,
            "amount": totals["total"],
            "token": response["token"],
            "url": response["url"],
            "redirect_url": redirect_url,
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



    status = result.get("status")

    return HTMLResponse(
        f"""
        <html>
            <head>
                <title>Volviendo a Ischuu...</title>
                <meta charset="UTF-8" />
            </head>

            <body style="font-family: Arial; padding: 20px;">
                <p>Volviendo a Ischuu...</p>

                <script>
                    setTimeout(function() {{
                        window.open('', '_self');
                        window.close();
                    }}, 300);

                    setTimeout(function() {{
                        document.body.innerHTML = "<p>Ya puedes cerrar esta ventana y volver a Ischuu.</p>";
                    }}, 1500);
                </script>
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
        print("WEBPAY FAILED DETAIL:", tx)

        return {
            "status": status,
            "total": payment.get("total", 0),
            "points_earned": 0,
            "response_code": tx.get("response_code"),
            "vci": tx.get("vci"),
            "buy_order": tx.get("buy_order"),
            "authorization_code": tx.get("authorization_code"),
            "payment_type_code": tx.get("payment_type_code"),
            "installments_number": tx.get("installments_number"),
        }

    existing_order = await db.orders.find_one({"webpay_token": token})
    if existing_order:
        return {
            "status": "AUTHORIZED",
            "order_id": str(existing_order["_id"]),
            "total": existing_order.get("total", 0),
            "points_earned": existing_order.get("points_earned", 0),
            "response_code": tx.get("response_code"),
            "vci": tx.get("vci"),
            "buy_order": tx.get("buy_order"),
            "authorization_code": tx.get("authorization_code"),
            "payment_type_code": tx.get("payment_type_code"),
            "installments_number": tx.get("installments_number"),
        }

    # Buscar datos del usuario dueño del pago
    user_doc = await db.users.find_one(
        {"_id": ObjectId(payment["user_id"])}
    )

    user_email = user_doc.get("email", "") if user_doc else ""
    user_name = user_doc.get("name", "") if user_doc else ""

    points_earned = earned_points_for_amount(
        int(payment.get("product_amount_paid", 0))
    )

    points_to_spend = int(payment.get("points_to_spend", 0))
    points_balance_change = points_earned - points_to_spend

    order = {
        "user_id": payment["user_id"],
        "user_email": user_email,
        "user_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "items": payment["items"],

        "shipping_address": payment.get("shipping_address", {}),
        "shipping_address_text": payment.get("shipping_address_text", ""),

        "subtotal": payment.get("subtotal", 0),
        "shipping": payment.get("shipping", 0),
        "discount": payment.get("discount", 0),
        "total": payment.get("total", 0),
        "status": "Compra realizada",
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

        preferences_inc[f"preferences.{category}"] = (
            preferences_inc.get(f"preferences.{category}", 0)
            + int(item.get("quantity", 1))
        )

        await db.products.update_one(
            {"_id": ObjectId(item["product_id"])},
            {
                "$inc": {
                    "stock": -int(item.get("quantity", 1))
                }
            },
        )

    await db.users.update_one(
        {"_id": ObjectId(payment["user_id"])},
        {
            "$inc": {
                "points": points_balance_change,
                **preferences_inc,
            }
        },
    )

    await db.payments.update_one(
        {"token": token},
        {
            "$set": {
                "order_id": str(result.inserted_id),
                "order_created": True,
            }
        },
    )

    created_order = {
        **order,
        "_id": result.inserted_id,
    }
    await send_order_status_push(created_order, "Compra realizada")

    return {
        "status": "AUTHORIZED",
        "order_id": str(result.inserted_id),
        "total": payment.get("total", 0),
        "points_earned": points_earned,
        "response_code": tx.get("response_code"),
        "vci": tx.get("vci"),
        "buy_order": tx.get("buy_order"),
        "authorization_code": tx.get("authorization_code"),
        "payment_type_code": tx.get("payment_type_code"),
        "installments_number": tx.get("installments_number"),
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

@router.get("/webpay/redirect/{token}", response_class=HTMLResponse)
async def webpay_redirect(token: str):
    payment = await db.payments.find_one({"token": token})

    if payment is None:
        return HTMLResponse(
            "<h2>Pago no encontrado</h2><p>No se encontró la transacción.</p>",
            status_code=404,
        )

    webpay_url = payment.get("webpay_url")

    if not webpay_url:
        return HTMLResponse(
            "<h2>Error Webpay</h2><p>No se encontró la URL de Webpay.</p>",
            status_code=500,
        )

    return HTMLResponse(
        f"""
        <html>
            <body>
                <p>Redirigiendo a Webpay...</p>

                <form id="webpay-form" method="POST" action="{webpay_url}">
                    <input type="hidden" name="token_ws" value="{token}" />
                </form>

                <script>
                    document.getElementById("webpay-form").submit();
                </script>
            </body>
        </html>
        """
    )
