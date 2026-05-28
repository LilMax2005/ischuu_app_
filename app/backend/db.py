from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorClient
from app.backend.core.config import settings

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_database]

async def ping_mongodb() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False
