from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.backend.db import db
from app.backend.dependencies import get_current_active_user
from app.backend.models import serialize_order

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.get("")
async def list_orders(user: dict = Depends(get_current_active_user)):
    orders = await db.orders.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(length=100)
    return [serialize_order(order) for order in orders]


@router.get("/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_active_user)):
    try:
        object_id = ObjectId(order_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID de pedido inválido") from exc
    order = await db.orders.find_one({"_id": object_id, "user_id": str(user["_id"])})
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return serialize_order(order)
