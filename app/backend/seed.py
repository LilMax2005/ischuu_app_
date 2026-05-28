import asyncio
from datetime import datetime, timezone

from app.backend.core.security import get_password_hash
from app.backend.db import database


PRODUCTS = [
    {
        "name": "Blind Box Naruto Shippuden",
        "series": "Naruto",
        "description": "Caja sorpresa con figuras coleccionables de Naruto.",
        "category": "Anime",
        "rarity": "Épica",
        "image_url": "https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=800",
        "price": 12990.0,
        "stock": 10,
        "is_original": True,
        "is_active": True,
    },
    {
        "name": "Blind Box One Piece Wanted",
        "series": "One Piece",
        "description": "Colección inspirada en personajes icónicos de One Piece.",
        "category": "Anime",
        "rarity": "Legendaria",
        "image_url": "https://images.unsplash.com/photo-1569705466238-7fef662aa89b?w=800",
        "price": 14990.0,
        "stock": 8,
        "is_original": True,
        "is_active": True,
    },
]


async def seed() -> None:
    await database.users.create_index("email", unique=True)
    admin = await database.users.find_one({"email": "admin@ischuu.cl"})
    if not admin:
        await database.users.insert_one(
            {
                "name": "Admin Ischuu",
                "email": "admin@ischuu.cl",
                "password_hash": get_password_hash("Admin1234"),
                "is_admin": True,
                "is_active": True,
                "points": 0,
                "created_at": datetime.now(timezone.utc),
            }
        )

    for payload in PRODUCTS:
        existing = await database.products.find_one({"name": payload["name"]})
        if not existing:
            product = dict(payload)
            product["created_at"] = datetime.now(timezone.utc)
            await database.products.insert_one(product)

    print("Seed MongoDB completado")


if __name__ == "__main__":
    asyncio.run(seed())
