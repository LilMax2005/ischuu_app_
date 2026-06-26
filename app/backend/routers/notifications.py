from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.backend.core.config import settings
from app.backend.dependencies import get_current_active_user
from app.backend.services.push_notifications import send_order_status_push


router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/config")
async def notification_config() -> dict:
    configured = bool(settings.onesignal_app_id)
    delivery_configured = bool(
        settings.onesignal_app_id and settings.onesignal_rest_api_key
    )
    return {
        "enabled": configured,
        "delivery_enabled": delivery_configured,
        "provider": "onesignal" if configured else "",
        "app_id": settings.onesignal_app_id if configured else "",
    }


@router.post("/test")
async def test_notification(user: dict = Depends(get_current_active_user)) -> dict:
    result = await send_order_status_push(
        {
            "_id": f"test-{uuid4().hex}",
            "user_id": str(user["_id"]),
            "buy_order": "PRUEBA",
        },
        "Pagado",
    )
    if not result.get("sent"):
        provider_detail = str(result.get("provider_detail", "")).strip()
        reason = str(result.get("reason", "error desconocido"))
        detail = provider_detail or f"Error de notificaciones: {reason}"
        raise HTTPException(
            status_code=503,
            detail=detail,
        )
    if int(result.get("recipients", 0)) < 1:
        raise HTTPException(
            status_code=409,
            detail="OneSignal no encontró un teléfono vinculado a esta cuenta",
        )
    return {"message": "Notificación de prueba enviada", **result}
