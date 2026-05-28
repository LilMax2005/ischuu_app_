from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException

from app.backend.core.security import decode_token
from app.backend.db import db

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    return await decode_token(authorization.replace("Bearer ", "").strip())


def serialize_order(order: dict) -> dict:
    return {
        "id": str(order["_id"]),
        "user_id": order.get("user_id", ""),
        "created_at": order.get("created_at", ""),
        "items": order.get("items", []),
        "shipping_address": order.get("shipping_address", {}),
        "shipping_address_text": order.get("shipping_address_text", ""),
        "user_email": order.get("user_email", ""),
        "user_name": order.get("user_name", ""),
        "subtotal": int(order.get("subtotal", 0)),
        "shipping": int(order.get("shipping", 0)),
        "discount": int(order.get("discount", 0)),
        "total": int(order.get("total", 0)),
        "status": order.get("status", "Compra realizada"),
        "payment_status": order.get("payment_status", ""),
        "points_earned": int(order.get("points_earned", 0)),
        "buy_order": order.get("buy_order", ""),
        "status_history": order.get("status_history", []),
    }


@router.get("")
async def list_orders(user: dict = Depends(current_user)):
    orders = await db.orders.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(length=100)
    return [serialize_order(order) for order in orders]


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: dict,
    user: dict = Depends(current_user),
):
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Solo el administrador puede modificar el seguimiento")

    new_status = str(payload.get("status", "")).strip()
    allowed_statuses = ["Pagado", "Preparando", "En despacho", "Entregado", "Cancelado"]

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Estados permitidos: {', '.join(allowed_statuses)}",
        )

    try:
        oid = ObjectId(order_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID de pedido inválido") from exc

    result = await db.orders.update_one(
        {"_id": oid},
        {"$set": {"status": new_status, "updated_by_admin": str(user["_id"])}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return {"message": "Estado actualizado correctamente", "order_id": order_id, "status": new_status}
