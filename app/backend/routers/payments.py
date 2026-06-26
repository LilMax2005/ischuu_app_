from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.backend.core.config import settings
from app.backend.db import db
from app.backend.dependencies import get_current_active_user
from app.backend.schemas import CartPaymentRequest, CartQuoteRequest
from app.backend.services.cart import enrich_cart_items
from app.backend.services.checkout import (
    CheckoutConflictError,
    PaymentValidationError,
    create_order_after_authorization,
)
from app.backend.services.pricing import calculate_cart_totals
from app.backend.services.shipping import normalize_shipping_address
from app.backend.services.transbank import commit_transaction, create_webpay_transaction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


def item_dicts(payload: CartQuoteRequest) -> list[dict]:
    return [item.model_dump() for item in payload.items]


async def committed_transaction(token: str) -> dict:
    """Evita volver a ejecutar el commit remoto para un pedido ya creado."""
    payment = await db.payments.find_one({"token": token})
    stored = payment.get("transaction") if payment else None
    if payment and payment.get("order_created") and isinstance(stored, dict):
        return stored
    return commit_transaction(token)


@router.post("/webpay/quote")
async def quote_cart_payment(
    payload: CartQuoteRequest,
    user: dict = Depends(get_current_active_user),
):
    enriched_items = await enrich_cart_items(db, item_dicts(payload))
    totals = calculate_cart_totals(
        enriched_items,
        user,
        use_points=payload.use_points,
        requested_points=payload.requested_points,
    )
    return {"items": enriched_items, **totals}


@router.post("/webpay/cart", status_code=201)
async def create_cart_payment(
    payload: CartPaymentRequest,
    user: dict = Depends(get_current_active_user),
):
    enriched_items = await enrich_cart_items(db, item_dicts(payload))
    try:
        shipping_address = normalize_shipping_address(user.get("shipping_address", {}) or {})
    except HTTPException as exc:
        detail = "Debes registrar una dirección de entrega válida antes de realizar el pago."
        if exc.detail:
            detail = f"{detail} {exc.detail}"
        raise HTTPException(status_code=400, detail=detail) from exc
    totals = calculate_cart_totals(
        enriched_items,
        user,
        use_points=payload.use_points,
        requested_points=payload.requested_points,
    )
    if int(totals["total"]) <= 0:
        raise HTTPException(status_code=400, detail="El total del carrito debe ser mayor que cero")

    buy_order = f"ISCHUU-{uuid.uuid4().hex[:10].upper()}"
    base_url = settings.api_base_url.rstrip("/")
    return_url = f"{base_url}/api/v1/payments/webpay/return"
    try:
        response = create_webpay_transaction(
            buy_order=buy_order,
            session_id=str(user["_id"]),
            amount=int(totals["total"]),
            return_url=return_url,
        )
    except Exception as exc:
        logger.exception("No se pudo crear la transacción Webpay")
        raise HTTPException(
            status_code=502,
            detail="Webpay no pudo iniciar la transacción. Intenta nuevamente.",
        ) from exc

    payment = {
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
        "status": "CREATED",
        "payment_method": "Webpay",
        "token": response["token"],
        "webpay_url": response.get("url"),
        "order_created": False,
        "processing_order": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payments.insert_one(payment)
    redirect_url = f"{base_url}/api/v1/payments/webpay/redirect/{response['token']}"
    return {
        "buy_order": buy_order,
        "amount": totals["total"],
        "token": response["token"],
        "url": response["url"],
        "redirect_url": redirect_url,
        **totals,
    }


@router.post("/webpay/commit")
async def commit_payment(payload: dict):
    token = str(payload.get("token", "")).strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token requerido")
    try:
        transaction = await committed_transaction(token)
    except Exception as exc:
        logger.exception("Webpay rechazó el commit del token")
        raise HTTPException(status_code=502, detail="No se pudo confirmar el pago con Webpay") from exc
    return await finalize_payment(token, transaction)


@router.api_route("/webpay/return", methods=["GET", "POST"], response_class=HTMLResponse)
async def webpay_return(request: Request):
    data = dict(request.query_params)
    if request.method == "POST":
        form = await request.form()
        data.update(dict(form))
    token = str(data.get("token_ws", "")).strip()
    if not token:
        return HTMLResponse("<h2>Pago cancelado</h2><p>No se recibió token_ws.</p>", status_code=400)

    try:
        transaction = await committed_transaction(token)
        result = await finalize_payment(token, transaction)
    except HTTPException as exc:
        return HTMLResponse(
            f"<h2>No fue posible completar el pedido</h2><p>{escape(str(exc.detail))}</p>",
            status_code=exc.status_code,
        )
    except Exception:
        logger.exception("Error inesperado confirmando el retorno de Webpay")
        return HTMLResponse(
            "<h2>Error al confirmar el pago</h2><p>El equipo de Ischuu debe revisar la transacción.</p>",
            status_code=500,
        )

    status = escape(str(result.get("status", "")))
    return HTMLResponse(
        f"""
        <html><head><meta charset="UTF-8"><title>Pago Ischuu</title></head>
        <body style="font-family:Arial;padding:24px">
          <h2>Estado del pago: {status}</h2>
          <p>Ya puedes cerrar esta ventana y volver a Ischuu.</p>
          <script>setTimeout(function(){{ window.close(); }}, 1200);</script>
        </body></html>
        """
    )


async def finalize_payment(token: str, transaction: dict) -> dict:
    payment = await db.payments.find_one({"token": token})
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    status_value = str(transaction.get("status", "")).upper()
    confirmed_amount = int(transaction.get("amount") or 0)
    await db.payments.update_one(
        {"token": token},
        {
            "$set": {
                "status": status_value,
                "amount_confirmed": confirmed_amount,
                "transaction": transaction,
                "committed_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    if status_value != "AUTHORIZED":
        return {
            "status": status_value or "REJECTED",
            "total": int(payment.get("total", 0)),
            "points_earned": 0,
            "order_created": False,
            "response_code": transaction.get("response_code"),
        }

    try:
        order = await create_order_after_authorization(db, payment, transaction)
    except PaymentValidationError as exc:
        await db.payments.update_one(
            {"token": token},
            {"$set": {"status": "VALIDATION_FAILED", "requires_manual_review": True, "fulfillment_error": str(exc)}},
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CheckoutConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "status": "AUTHORIZED",
        "order_id": str(order["_id"]),
        "order_created": True,
        "total": int(order.get("total", 0)),
        "points_earned": int(order.get("points_earned", 0)),
        "response_code": transaction.get("response_code"),
        "authorization_code": transaction.get("authorization_code"),
    }


@router.get("/webpay/status/{token}")
async def get_payment_status(
    token: str,
    user: dict = Depends(get_current_active_user),
):
    payment = await db.payments.find_one({"token": token})
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if payment.get("user_id") != str(user["_id"]) and not bool(user.get("is_admin", False)):
        raise HTTPException(status_code=403, detail="No autorizado")
    return {
        "token": token,
        "status": payment.get("status", "CREATED"),
        "order_created": bool(payment.get("order_created", False)),
        "order_id": payment.get("order_id"),
        "amount": int(payment.get("amount", 0)),
        "total": int(payment.get("total", 0)),
        "requires_manual_review": bool(payment.get("requires_manual_review", False)),
        "fulfillment_error": payment.get("fulfillment_error", ""),
    }


@router.get("/webpay/redirect/{token}", response_class=HTMLResponse)
async def webpay_redirect(token: str):
    payment = await db.payments.find_one({"token": token})
    if payment is None:
        return HTMLResponse("<h2>Pago no encontrado</h2>", status_code=404)
    webpay_url = str(payment.get("webpay_url", ""))
    if not webpay_url:
        return HTMLResponse("<h2>Webpay no entregó una URL de pago</h2>", status_code=502)
    return HTMLResponse(
        f"""
        <html><body><p>Redirigiendo a Webpay...</p>
        <form id="webpay-form" method="POST" action="{escape(webpay_url, quote=True)}">
          <input type="hidden" name="token_ws" value="{escape(token, quote=True)}">
        </form>
        <script>document.getElementById('webpay-form').submit();</script>
        </body></html>
        """
    )
