from __future__ import annotations

from fastapi import APIRouter

from app.backend.core.config import settings


router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/config")
async def notification_config() -> dict:
    configured = bool(settings.onesignal_app_id)
    return {
        "enabled": configured,
        "provider": "onesignal" if configured else "",
        "app_id": settings.onesignal_app_id if configured else "",
    }
