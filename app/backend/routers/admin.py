from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
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


def regex_filter(value: str) -> dict:
    return {"$regex": re.escape(value.strip()), "$options": "i"}


def parse_date(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{label} debe tener formato YYYY-MM-DD") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def order_date_bounds(
    *,
    date: str = "",
    start_date: str = "",
    end_date: str = "",
    period: str = "",
    year: int | None = None,
) -> tuple[str, str] | None:
    now = datetime.now(timezone.utc)
    period = period.strip().lower()

    if date.strip():
        start = parse_date(date.strip(), "date")
        end = start + timedelta(days=1)
    elif start_date.strip() or end_date.strip():
        start = (
            parse_date(start_date.strip(), "start_date")
            if start_date.strip()
            else datetime.min.replace(tzinfo=timezone.utc)
        )
        end = (
            parse_date(end_date.strip(), "end_date") + timedelta(days=1)
            if end_date.strip()
            else datetime.max.replace(tzinfo=timezone.utc)
        )
    elif period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        end = start + timedelta(days=7)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
    elif period == "year" or year:
        selected_year = int(year or now.year)
        start = datetime(selected_year, 1, 1, tzinfo=timezone.utc)
        end = datetime(selected_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        return None

    if end <= start:
        raise HTTPException(status_code=400, detail="La fecha final debe ser posterior a la inicial")

    return start.isoformat(), end.isoformat()


def build_order_filters(
    *,
    search: str = "",
    status: str = "",
    payment_method: str = "",
    payment_status: str = "",
    product: str = "",
    category: str = "",
    date: str = "",
    start_date: str = "",
    end_date: str = "",
    period: str = "",
    year: int | None = None,
) -> dict:
    conditions: list[dict] = []

    search = search.strip()
    if search:
        search_conditions = [
            {"buy_order": regex_filter(search)},
            {"user_name": regex_filter(search)},
            {"user_email": regex_filter(search)},
            {"status": regex_filter(search)},
            {"payment_status": regex_filter(search)},
            {"payment_method": regex_filter(search)},
            {"items.name": regex_filter(search)},
            {"items.category": regex_filter(search)},
        ]
        if ObjectId.is_valid(search):
            search_conditions.append({"_id": ObjectId(search)})
        conditions.append({"$or": search_conditions})

    status = status.strip()
    if status and status != "Todos":
        conditions.append({"status": status})

    payment_method = payment_method.strip()
    if payment_method and payment_method != "Todos":
        if payment_method.lower() == "webpay":
            conditions.append(
                {
                    "$or": [
                        {"payment_method": regex_filter("Webpay")},
                        {"webpay_token": {"$exists": True}},
                        {"buy_order": {"$regex": "^ISCHUU-", "$options": "i"}},
                    ]
                }
            )
        else:
            conditions.append({"payment_method": regex_filter(payment_method)})

    payment_status = payment_status.strip()
    if payment_status and payment_status != "Todos":
        conditions.append({"payment_status": regex_filter(payment_status)})

    product = product.strip()
    if product:
        conditions.append({"items.name": regex_filter(product)})

    category = category.strip()
    if category:
        conditions.append({"items.category": regex_filter(category)})

    bounds = order_date_bounds(
        date=date,
        start_date=start_date,
        end_date=end_date,
        period=period,
        year=year,
    )
    if bounds is not None:
        start, end = bounds
        conditions.append({"created_at": {"$gte": start, "$lt": end}})

    if not conditions:
        return {}

    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


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
async def list_orders(
    _: dict = Depends(get_current_admin),
    search: str = "",
    status: str = "",
    payment_method: str = "",
    payment_status: str = "",
    product: str = "",
    category: str = "",
    date: str = "",
    start_date: str = "",
    end_date: str = "",
    period: str = "",
    year: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    filters = build_order_filters(
        search=search,
        status=status,
        payment_method=payment_method,
        payment_status=payment_status,
        product=product,
        category=category,
        date=date,
        start_date=start_date,
        end_date=end_date,
        period=period,
        year=year,
    )
    total = await db.orders.count_documents(filters)
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    current_page = min(page, total_pages)
    orders = await db.orders.find(filters).sort("created_at", -1).skip(
        (current_page - 1) * page_size
    ).to_list(length=page_size)
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
    return {
        "items": results,
        "page": current_page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


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
