from __future__ import annotations

from fastapi import APIRouter, Depends

from app.backend.db import db
from app.backend.dependencies import get_current_admin
from app.backend.models import serialize_product
from app.backend.services.catalog import CATALOG

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("")
async def list_products():
    products = await db.products.find().sort([("category", 1), ("name", 1)]).to_list(length=500)
    return [serialize_product(product) for product in products]


@router.post("/seed")
async def seed_products(_: dict = Depends(get_current_admin)):
    await db.products.delete_many({})
    await db.products.insert_many(CATALOG)
    return {"message": "Catálogo cargado correctamente", "items": len(CATALOG)}
