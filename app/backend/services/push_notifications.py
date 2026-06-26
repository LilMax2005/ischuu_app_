from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

import httpx
from bson import ObjectId

from app.backend.core.config import settings
from app.backend.db import db


ONESIGNAL_NOTIFICATIONS_URL = "https://api.onesignal.com/notifications"

STATUS_MESSAGES = {
    "Pagado": (
        "¡Pago confirmado! 💗",
        "Recibimos tu compra y ya comenzamos a prepararla.",
    ),
    "Preparando": (
        "Estamos preparando tu pedido 📦",
        "Tu compra está siendo preparada para despacho.",
    ),
    "En despacho": (
        "Tu pedido va en camino 🚚",
        "Tu compra fue enviada. Revisa su avance en la app.",
    ),
    "Entregado": (
        "¡Pedido entregado! ✨",
        "Tu compra figura como entregada. Esperamos que la disfrutes.",
    ),
    "Cancelado": (
        "Pedido cancelado",
        "El pedido figura como cancelado. Contáctanos si necesitas ayuda.",
    ),
    "Compra realizada": (
        "¡Compra confirmada! 💗",
        "Recibimos tu compra y ya comenzamos a prepararla.",
    ),
    "Artículo empaquetado": (
        "Tu pedido está empaquetado 📦",
        "Tu compra está lista y esperando ser despachada.",
    ),
    "Artículo enviado": (
        "Tu pedido va en camino 🚚",
        "Tu compra fue enviada. Revisa su avance en la app.",
    ),
    "Artículo entregado": (
        "¡Pedido entregado! ✨",
        "Tu compra figura como entregada. Esperamos que la disfrutes.",
    ),
}


def onesignal_error_detail(response: httpx.Response) -> str:
    if response.status_code == 401:
        return "La REST API Key de OneSignal fue rechazada"
    if response.status_code == 403:
        return "OneSignal rechazó el acceso a esta aplicación"

    try:
        data = response.json()
        errors = data.get("errors") if isinstance(data, dict) else None
        if isinstance(errors, list):
            detail = "; ".join(str(item) for item in errors)
        elif errors:
            detail = str(errors)
        elif isinstance(data, dict) and data.get("error"):
            detail = str(data["error"])
        else:
            detail = ""
    except Exception:
        detail = ""

    return detail[:400] or f"OneSignal respondió con HTTP {response.status_code}"


def build_order_push_payload(order: dict, status: str) -> dict | None:
    message = STATUS_MESSAGES.get(status)
    user_id = str(order.get("user_id", "")).strip()

    if message is None or not user_id:
        return None

    order_id = str(order.get("_id", order.get("id", ""))).strip()
    order_number = str(order.get("buy_order", "")).strip()
    visible_number = order_number or order_id[-8:].upper()
    title, body = message

    if visible_number:
        body = f"{body} Pedido #{visible_number}."

    idempotency_source = f"ischuu:{order_id or visible_number}:{status}"

    return {
        "app_id": settings.onesignal_app_id,
        "target_channel": "push",
        "include_aliases": {"external_id": [user_id]},
        "headings": {"en": title, "es": title},
        "contents": {"en": body, "es": body},
        "data": {
            "type": "order_status",
            "order_id": order_id,
            "status": status,
            "route": "orders",
        },
        "idempotency_key": str(uuid5(NAMESPACE_URL, idempotency_source)),
    }


async def send_order_status_push(order: dict, status: str) -> dict:
    if not settings.onesignal_app_id or not settings.onesignal_rest_api_key:
        return {"sent": False, "reason": "onesignal_not_configured"}

    payload = build_order_push_payload(order, status)
    if payload is None:
        return {"sent": False, "reason": "invalid_order_or_status"}

    user_id = str(order.get("user_id", "")).strip()

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None

    if user is None:
        return {"sent": False, "reason": "user_not_found"}

    if not bool(user.get("notifications_enabled", True)):
        return {"sent": False, "reason": "notifications_disabled"}

    headers = {
        "Accept": "application/json",
        "Authorization": f"Key {settings.onesignal_rest_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                ONESIGNAL_NOTIFICATIONS_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "sent": True,
            "notification_id": data.get("id", ""),
            "recipients": int(data.get("recipients", 0) or 0),
        }
    except httpx.HTTPStatusError as exc:
        detail = onesignal_error_detail(exc.response)
        print(
            f"OneSignal rechazó el push del pedido {order.get('_id', '')}: "
            f"HTTP {exc.response.status_code} - {detail}"
        )
        return {
            "sent": False,
            "reason": "provider_error",
            "provider_status": exc.response.status_code,
            "provider_detail": detail,
        }
    except httpx.RequestError as exc:
        print(f"No se pudo conectar con OneSignal: {exc}")
        return {
            "sent": False,
            "reason": "provider_unavailable",
            "provider_detail": "No fue posible conectar con OneSignal",
        }
    except Exception as exc:
        print(f"No se pudo enviar push del pedido {order.get('_id', '')}: {exc}")
        return {
            "sent": False,
            "reason": "provider_error",
            "provider_detail": "Error inesperado al enviar la notificación",
        }
