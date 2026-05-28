from __future__ import annotations
from fastapi import APIRouter
from app.backend.db import db
from app.backend.services.catalog import CATALOG

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

def serialize_product(p: dict) -> dict:
    return {"id": str(p["_id"]), "name": p["name"], "series": p.get("series", ""), "category": p.get("category", "General"), "rarity": p.get("rarity", "Común"), "price": int(p.get("price", 0)), "stock": int(p.get("stock", 0)), "is_original": bool(p.get("is_original", True)), "description": p.get("description", ""), "image_url": p.get("image_url", "")}

@router.get("")
async def list_products():
    products = await db.products.find().sort("category", 1).to_list(length=500)
    return [serialize_product(p) for p in products]

@router.post("/seed")
async def seed_products():
    await db.products.delete_many({})
    await db.products.insert_many(CATALOG)
    return {"message": "Catálogo cargado correctamente", "items": len(CATALOG)}
