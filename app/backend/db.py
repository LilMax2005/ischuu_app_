from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from app.backend.core.config import settings

client = AsyncIOMotorClient(
    settings.mongodb_url,
    tls=True,
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