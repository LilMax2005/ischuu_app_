from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from app.backend.core.config import settings

use_tls = settings.mongodb_tls
if use_tls is None:
    use_tls = settings.mongodb_url.lower().startswith("mongodb+srv://")

client = AsyncIOMotorClient(
    settings.mongodb_url,
    tls=use_tls,
    serverSelectionTimeoutMS=30000,
)

db = client[settings.mongodb_database]


async def ping_mongodb() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception as exc:
        print("MongoDB ping error:", exc)
        return False
