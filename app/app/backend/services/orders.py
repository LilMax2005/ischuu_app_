from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from bson import ObjectId
from fastapi import HTTPException

from app.backend.models import ORDER_STATUSES, normalize_order_status
from app.backend.services.email import send_email
from app.backend.services.push_notifications import send_order_status_push


async def change_order_status(
    database,
    order_id: ObjectId,
    new_status: str,
    admin: dict,
) -> dict:
    new_status = normalize_order_status(new_status)
    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Permitidos: {', '.join(ORDER_STATUSES)}",
        )

    order = await database.orders.find_one({"_id": order_id})
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    old_status = normalize_order_status(order.get("status"))
    if old_status == new_status:
        return order

    changed_at = datetime.now(timezone.utc).isoformat()
    history = {
        "from": old_status,
        "to": new_status,
        "changed_at": changed_at,
        "changed_by": admin.get("email", "admin"),
    }
    await database.orders.update_one(
        {"_id": order_id},
        {"$set": {"status": new_status}, "$push": {"status_history": history}},
    )
    updated = await database.orders.find_one({"_id": order_id})

    email = str(updated.get("user_email", ""))
    customer = str(updated.get("user_name", "") or "Cliente")
    if (not email or customer == "Cliente") and updated.get("user_id"):
        try:
            user = await database.users.find_one({"_id": ObjectId(updated["user_id"])})
        except Exception:
            user = None
        if user:
            email = email or str(user.get("email", ""))
            customer = str(user.get("name", customer))

    if email:
        visible_id = str(order_id)[-8:].upper()
        address = updated.get("shipping_address_text", "Dirección no disponible")
        subject = f"Actualización de tu pedido Ischuu #{visible_id}"
        text = (
            f"Hola {customer},\n\n"
            f"Tu pedido cambió de {old_status} a {new_status}.\n"
            f"Seguimiento: {visible_id}\n"
            f"Dirección: {address}\n\n"
            "Gracias por comprar en Ischuu."
        )
        html = (
            "<h2>Actualización de pedido Ischuu</h2>"
            f"<p>Hola {escape(customer)},</p>"
            f"<p>Tu pedido cambió de <strong>{escape(old_status)}</strong> "
            f"a <strong>{escape(new_status)}</strong>.</p>"
            f"<p>Seguimiento: {escape(visible_id)}</p>"
        )
        send_email(email, subject, text, html)

    await send_order_status_push(updated, new_status)
    return updated
