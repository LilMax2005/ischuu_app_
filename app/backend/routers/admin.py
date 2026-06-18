from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.backend.core.config import settings
from app.backend.db import db
from app.backend.dependencies import get_current_admin
from app.backend.models import ORDER_STATUSES, serialize_order, serialize_product, serialize_user
from app.backend.schemas import (
    AdminUserUpdate,
    OrderStatusUpdate,
    ProductCreate,
    ProductUpdate,
    SocialSettingsUpdate,
    StockUpdate,
)
from app.backend.services.exporter import export_orders_to_excel
from app.backend.services.orders import change_order_status

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


def object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID inválido") from exc


@router.get("/summary")
async def admin_summary(_: dict = Depends(get_current_admin)):
    """Resumen consistente entre tarjetas y desglose de estados.

    Los estados logísticos se calculan únicamente sobre pedidos con pago
    aprobado. Así, la suma del desglose coincide con ``paid_orders``.
    """
    orders = await db.orders.find().to_list(length=5000)
    paid_orders = [
        order
        for order in orders
        if str(order.get("payment_status", "")).lower() == "paid"
    ]

    status_counts = {status: 0 for status in ORDER_STATUSES}
    for order in paid_orders:
        serialized_status = serialize_order(order)["status"]
        status_counts[serialized_status] = status_counts.get(serialized_status, 0) + 1

    return {
        "users": await db.users.count_documents({}),
        "products": await db.products.count_documents({}),
        "orders": len(orders),
        "paid_orders": len(paid_orders),
        "status_total": sum(status_counts.values()),
        "revenue": sum(int(order.get("total", 0)) for order in paid_orders),
        "low_stock": await db.products.count_documents({"stock": {"$lte": 3}}),
        "status_counts": status_counts,
        "statuses": ORDER_STATUSES,
    }


@router.get("/users")
async def list_users(_: dict = Depends(get_current_admin)):
    users = await db.users.find().sort("email", 1).to_list(length=1000)
    return [serialize_user(user) for user in users]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    admin: dict = Depends(get_current_admin),
):
    target_id = object_id(user_id)
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")

    if target_id == admin["_id"]:
        if data.get("is_active") is False:
            raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
        if data.get("is_admin") is False:
            raise HTTPException(status_code=400, detail="No puedes quitarte tus propios permisos")

    result = await db.users.update_one({"_id": target_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(await db.users.find_one({"_id": target_id}))


@router.get("/products")
async def list_products(_: dict = Depends(get_current_admin)):
    products = await db.products.find().sort([("category", 1), ("name", 1)]).to_list(length=1000)
    return [serialize_product(product) for product in products]


@router.post("/products", status_code=201)
async def create_product(payload: ProductCreate, _: dict = Depends(get_current_admin)):
    document = payload.model_dump()
    document.update(
        {
            "name": payload.name.strip(),
            "category": payload.category.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    result = await db.products.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_product(document)


@router.patch("/products/{product_id}")
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    _: dict = Depends(get_current_admin),
):
    target_id = object_id(product_id)
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.products.update_one({"_id": target_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serialize_product(await db.products.find_one({"_id": target_id}))


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, _: dict = Depends(get_current_admin)):
    result = await db.products.delete_one({"_id": object_id(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado correctamente"}


@router.patch("/products/{product_id}/stock")
async def update_product_stock(
    product_id: str,
    payload: StockUpdate,
    _: dict = Depends(get_current_admin),
):
    target_id = object_id(product_id)
    if payload.operation == "add":
        if payload.quantity is None:
            raise HTTPException(status_code=400, detail="quantity es obligatorio para add")
        update = {"$inc": {"stock": payload.quantity}}
    else:
        if payload.stock is None:
            raise HTTPException(status_code=400, detail="stock es obligatorio para set")
        update = {"$set": {"stock": payload.stock}}

    result = await db.products.update_one({"_id": target_id}, update)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product = await db.products.find_one({"_id": target_id})
    return serialize_product(product)


@router.post("/products/upload-image")
async def upload_product_image(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_admin),
):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Formato no permitido")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La imagen supera el máximo de 5 MB")
    folder = Path("app/backend/static/uploads")
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    (folder / filename).write_bytes(content)
    return {"image_url": f"{settings.api_base_url}/static/uploads/{filename}"}


@router.get("/orders")
async def list_orders(_: dict = Depends(get_current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(length=1000)
    results = []
    for order in orders:
        if order.get("user_id") and not order.get("user_email"):
            try:
                user = await db.users.find_one({"_id": ObjectId(order["user_id"])})
            except Exception:
                user = None
            if user:
                order = {**order, "user_email": user.get("email", ""), "user_name": user.get("name", "")}
        results.append(serialize_order(order))
    return results


@router.get("/orders/export")
async def export_orders(_: dict = Depends(get_current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(length=5000)
    path = export_orders_to_excel(orders)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="pedidos_ischuu.xlsx",
    )


@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str, _: dict = Depends(get_current_admin)):
    order = await db.orders.find_one({"_id": object_id(order_id)})
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return serialize_order(order)


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    admin: dict = Depends(get_current_admin),
):
    order = await change_order_status(db, object_id(order_id), payload.status, admin)
    return serialize_order(order)


@router.get("/settings")
async def get_settings(_: dict = Depends(get_current_admin)):
    document = await db.settings.find_one({"key": "social"})
    if document is None:
        return {
            "instagram_url": "https://www.instagram.com/ischuu._",
            "tiktok_url": "https://www.tiktok.com/",
            "instagram_enabled": False,
            "tiktok_enabled": False,
        }
    return {key: value for key, value in document.items() if key not in {"_id", "key"}}


@router.patch("/settings")
async def update_settings(
    payload: SocialSettingsUpdate,
    _: dict = Depends(get_current_admin),
):
    data = payload.model_dump()
    await db.settings.update_one({"key": "social"}, {"$set": data}, upsert=True)
    return data
