from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException

from app.backend.core.security import decode_token
from app.backend.db import db

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

ORDER_STATUSES = [
    "Compra realizada",
    "Artículo empaquetado",
    "Artículo enviado",
    "Artículo entregado",
]


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")

    return await decode_token(authorization.replace("Bearer ", "").strip())


async def current_admin(user: dict = Depends(current_user)) -> dict:
    email = str(user.get("email", "")).lower().strip()

    if not user.get("is_admin", False) and email != "admin@ischuu.cl":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede realizar esta acción",
        )

    return user


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID inválido") from exc


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "points": int(user.get("points", 0)),
        "is_admin": bool(user.get("is_admin", False)),
        "is_active": bool(user.get("is_active", True)),
        "preferences": user.get("preferences", {}) or {},
    }


def serialize_product(product: dict) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product.get("name", ""),
        "category": product.get("category", ""),
        "price": int(product.get("price", 0)),
        "stock": int(product.get("stock", 0)),
        "rarity": product.get("rarity", ""),
        "series": product.get("series", ""),
    }


def serialize_order(order: dict) -> dict:
    return {
        "id": str(order["_id"]),
        "user_id": order.get("user_id", ""),
        "created_at": order.get("created_at", ""),
        "items": order.get("items", []),
        "subtotal": int(order.get("subtotal", 0)),
        "shipping": int(order.get("shipping", 0)),
        "discount": int(order.get("discount", 0)),
        "total": int(order.get("total", 0)),
        "status": order.get("status", "Compra realizada"),
        "payment_status": order.get("payment_status", ""),
        "points_earned": int(order.get("points_earned", 0)),
        "buy_order": order.get("buy_order", ""),
    }


@router.get("/users")
async def list_users(_: dict = Depends(current_admin)):
    users = await db.users.find().sort("email", 1).to_list(length=1000)
    return [serialize_user(user) for user in users]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: dict,
    _: dict = Depends(current_admin),
):
    update_data = {}

    if "is_active" in payload:
        update_data["is_active"] = bool(payload["is_active"])

    if "is_admin" in payload:
        update_data["is_admin"] = bool(payload["is_admin"])

    if "points" in payload:
        update_data["points"] = max(0, int(payload["points"]))

    if not update_data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")

    result = await db.users.update_one(
        {"_id": to_object_id(user_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user = await db.users.find_one({"_id": to_object_id(user_id)})
    return serialize_user(user)


@router.get("/products")
async def list_products(_: dict = Depends(current_admin)):
    products = await db.products.find().sort("name", 1).to_list(length=1000)
    return [serialize_product(product) for product in products]


@router.patch("/products/{product_id}/stock")
async def update_product_stock(
    product_id: str,
    payload: dict,
    _: dict = Depends(current_admin),
):
    operation = str(payload.get("operation", "add")).lower().strip()

    if operation not in ["add", "set"]:
        raise HTTPException(
            status_code=400,
            detail="operation debe ser 'add' o 'set'",
        )

    if operation == "add":
        quantity = int(payload.get("quantity", 0))

        if quantity == 0:
            raise HTTPException(status_code=400, detail="quantity no puede ser 0")

        await db.products.update_one(
            {"_id": to_object_id(product_id)},
            {"$inc": {"stock": quantity}},
        )

    if operation == "set":
        stock = max(0, int(payload.get("stock", 0)))

        await db.products.update_one(
            {"_id": to_object_id(product_id)},
            {"$set": {"stock": stock}},
        )

    product = await db.products.find_one({"_id": to_object_id(product_id)})

    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return serialize_product(product)


@router.get("/orders")
async def list_orders(_: dict = Depends(current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(length=1000)
    return [serialize_order(order) for order in orders]


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: dict,
    _: dict = Depends(current_admin),
):
    new_status = str(payload.get("status", "")).strip()

    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Estados permitidos: {', '.join(ORDER_STATUSES)}",
        )

    result = await db.orders.update_one(
        {"_id": to_object_id(order_id)},
        {"$set": {"status": new_status}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    order = await db.orders.find_one({"_id": to_object_id(order_id)})
    return serialize_order(order)