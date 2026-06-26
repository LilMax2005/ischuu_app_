from __future__ import annotations

import math
import re

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.backend.db import db
from app.backend.dependencies import get_current_admin
from app.backend.models import serialize_product
from app.backend.services.catalog import CATALOG

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("")
async def list_products(
    search: str = "",
    category: str = "Todas",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    filters: dict = {}
    search = search.strip()
    category = category.strip()

    if category and category != "Todas":
        filters["category"] = category

    if search:
        pattern = {"$regex": re.escape(search), "$options": "i"}
        filters["$or"] = [
            {"name": pattern},
            {"series": pattern},
            {"category": pattern},
            {"rarity": pattern},
        ]

    total = await db.products.count_documents(filters)
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    current_page = min(page, total_pages)
    skip = (current_page - 1) * page_size
    products = await db.products.find(filters).sort(
        [("category", 1), ("name", 1)]
    ).skip(skip).to_list(length=page_size)
    categories = await db.products.distinct("category")

    return {
        "items": [serialize_product(product) for product in products],
        "page": current_page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "categories": sorted(category for category in categories if category),
    }


@router.get("/{product_id}")
async def get_product(product_id: str):
    try:
        object_id = ObjectId(product_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID de producto inválido") from exc

    product = await db.products.find_one({"_id": object_id})
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serialize_product(product)


@router.post("/seed")
async def seed_products(_: dict = Depends(get_current_admin)):
    await db.products.delete_many({})
    await db.products.insert_many(CATALOG)
    return {"message": "Catálogo cargado correctamente", "items": len(CATALOG)}
