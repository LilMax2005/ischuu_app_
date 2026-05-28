from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse


from app.backend.core.config import settings
from app.backend.core.security import decode_token
from app.backend.db import db
from app.backend.services.email import send_email
from app.backend.services.exporter import export_orders_to_excel

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

ORDER_STATUSES = ["Compra realizada", "Artículo empaquetado", "Artículo enviado", "Artículo entregado"]

def format_datetime_chile() -> str:
    now = datetime.now(timezone.utc)

    try:
        from zoneinfo import ZoneInfo

        now = now.astimezone(ZoneInfo("America/Santiago"))
    except Exception:
        pass

    return now.strftime("%d/%m/%Y %H:%M hrs")
async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    return await decode_token(authorization.replace("Bearer ", "").strip())

async def current_admin(user: dict = Depends(current_user)) -> dict:
    email = str(user.get("email", "")).lower().strip()
    if not user.get("is_admin", False) and email != "admin@ischuu.cl":
        raise HTTPException(status_code=403, detail="Solo el administrador puede realizar esta acción")
    return user

def oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ID inválido") from exc

def serialize_user(u: dict) -> dict:
    return {"id": str(u["_id"]), "name": u.get("name", ""), "email": u.get("email", ""), "points": int(u.get("points", 0)), "is_admin": bool(u.get("is_admin", False)), "is_active": bool(u.get("is_active", True)), "preferences": u.get("preferences", {}) or {}}

def serialize_product(p: dict) -> dict:
    return {"id": str(p["_id"]), "name": p.get("name", ""), "series": p.get("series", ""), "category": p.get("category", ""), "rarity": p.get("rarity", ""), "price": int(p.get("price", 0)), "stock": int(p.get("stock", 0)), "is_original": bool(p.get("is_original", True)), "description": p.get("description", ""), "image_url": p.get("image_url", "")}

def serialize_order(o: dict) -> dict:
    return {"id": str(o["_id"]), "user_id": o.get("user_id", ""), "user_email": o.get("user_email", ""), "created_at": o.get("created_at", ""), "items": o.get("items", []), "subtotal": int(o.get("subtotal", 0)), "shipping": int(o.get("shipping", 0)), "discount": int(o.get("discount", 0)), "total": int(o.get("total", 0)), "status": o.get("status", "Compra realizada"), "payment_status": o.get("payment_status", ""), "points_earned": int(o.get("points_earned", 0)), "buy_order": o.get("buy_order", ""), "status_history": o.get("status_history", [])}

@router.get("/summary")
async def admin_summary(_: dict = Depends(current_admin)):
    orders = await db.orders.find().to_list(length=5000)
    paid = [o for o in orders if o.get("payment_status") == "paid"]
    status_counts = {s: 0 for s in ORDER_STATUSES}
    for o in orders:
        s = o.get("status", "Compra realizada")
        status_counts[s] = status_counts.get(s, 0) + 1
    return {"users": await db.users.count_documents({}), "products": await db.products.count_documents({}), "orders": len(orders), "paid_orders": len(paid), "revenue": sum(int(o.get("total", 0)) for o in paid), "low_stock": await db.products.count_documents({"stock": {"$lte": 3}}), "status_counts": status_counts, "statuses": ORDER_STATUSES}

@router.get("/users")
async def list_users(_: dict = Depends(current_admin)):
    return [serialize_user(u) for u in await db.users.find().sort("email", 1).to_list(length=1000)]

@router.patch("/users/{user_id}")
async def update_user(user_id: str, payload: dict, _: dict = Depends(current_admin)):
    data = {}
    if "is_active" in payload: data["is_active"] = bool(payload["is_active"])
    if "is_admin" in payload: data["is_admin"] = bool(payload["is_admin"])
    if "points" in payload: data["points"] = max(0, int(payload["points"]))
    if not data: raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    r = await db.users.update_one({"_id": oid(user_id)}, {"$set": data})
    if r.matched_count == 0: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(await db.users.find_one({"_id": oid(user_id)}))

@router.get("/products")
async def list_products(_: dict = Depends(current_admin)):
    return [serialize_product(p) for p in await db.products.find().sort("name", 1).to_list(length=1000)]

@router.post("/products")
async def create_product(payload: dict, _: dict = Depends(current_admin)):
    for field in ["name", "price", "stock", "category"]:
        if field not in payload or payload[field] in [None, ""]:
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
    doc = {"name": str(payload.get("name", "")).strip(), "series": str(payload.get("series", "")).strip(), "category": str(payload.get("category", "General")).strip(), "rarity": str(payload.get("rarity", "Común")).strip(), "price": int(payload.get("price", 0)), "stock": int(payload.get("stock", 0)), "is_original": bool(payload.get("is_original", True)), "description": str(payload.get("description", "")).strip(), "image_url": str(payload.get("image_url", "")).strip(), "created_at": datetime.now(timezone.utc).isoformat()}
    res = await db.products.insert_one(doc); doc["_id"] = res.inserted_id
    return serialize_product(doc)

@router.patch("/products/{product_id}")
async def update_product(product_id: str, payload: dict, _: dict = Depends(current_admin)):
    allowed = {"name", "series", "category", "rarity", "price", "stock", "is_original", "description", "image_url"}
    data = {k: payload[k] for k in allowed if k in payload}
    if "price" in data: data["price"] = int(data["price"])
    if "stock" in data: data["stock"] = int(data["stock"])
    if not data: raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    r = await db.products.update_one({"_id": oid(product_id)}, {"$set": data})
    if r.matched_count == 0: raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serialize_product(await db.products.find_one({"_id": oid(product_id)}))

@router.delete("/products/{product_id}")
async def delete_product(product_id: str, _: dict = Depends(current_admin)):
    r = await db.products.delete_one({"_id": oid(product_id)})
    if r.deleted_count == 0: raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado correctamente"}

@router.patch("/products/{product_id}/stock")
async def update_product_stock(product_id: str, payload: dict, _: dict = Depends(current_admin)):
    op = str(payload.get("operation", "add")).lower().strip()
    if op == "add":
        await db.products.update_one({"_id": oid(product_id)}, {"$inc": {"stock": int(payload.get("quantity", 0))}})
    elif op == "set":
        await db.products.update_one({"_id": oid(product_id)}, {"$set": {"stock": max(0, int(payload.get("stock", 0)))}})
    else:
        raise HTTPException(status_code=400, detail="operation debe ser add o set")
    return serialize_product(await db.products.find_one({"_id": oid(product_id)}))

@router.post("/products/upload-image")
async def upload_product_image(file: UploadFile = File(...), _: dict = Depends(current_admin)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Formato no permitido")
    folder = Path("app/backend/static/uploads"); folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"; path = folder / filename
    path.write_bytes(await file.read())
    return {"image_url": f"{settings.api_base_url}/static/uploads/{filename}"}

@router.get("/orders")
async def list_orders(_: dict = Depends(current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(length=1000)
    for o in orders:
        if o.get("user_id") and not o.get("user_email"):
            try:
                u = await db.users.find_one({"_id": ObjectId(o["user_id"])}); o["user_email"] = u.get("email", "") if u else ""
            except Exception: pass
    return [serialize_order(o) for o in orders]

@router.get("/orders/export")
async def export_orders(_: dict = Depends(current_admin)):
    orders = await db.orders.find().sort("created_at", -1).to_list(length=5000)
    path = export_orders_to_excel(orders)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="pedidos_ischuu.xlsx")

@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str, _: dict = Depends(current_admin)):
    order = await db.orders.find_one({"_id": oid(order_id)})
    if not order: raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return serialize_order(order)

@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: dict,
    admin: dict = Depends(current_admin),
):


    new_status = str(payload.get("status", "")).strip()

    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido",
        )

    order = await db.orders.find_one(
        {"_id": oid(order_id)}
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    old_status = order.get("status", "Compra realizada")



    if old_status == new_status:

        return serialize_order(order)

    updated_at_iso = datetime.now(timezone.utc).isoformat()

    try:
        from zoneinfo import ZoneInfo

        updated_at_text = datetime.now(timezone.utc).astimezone(
            ZoneInfo("America/Santiago")
        ).strftime("%d/%m/%Y %H:%M hrs")
    except Exception:
        updated_at_text = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M hrs")

    hist = {
        "from": old_status,
        "to": new_status,
        "changed_at": updated_at_iso,
        "changed_by": admin.get("email", "admin"),
    }

    await db.orders.update_one(
        {"_id": oid(order_id)},
        {
            "$set": {
                "status": new_status,
            },
            "$push": {
                "status_history": hist,
            },
        },
    )

    user_email = order.get("user_email", "")
    customer_name = order.get("user_name", "") or "Cliente"

    if (not user_email or customer_name == "Cliente") and order.get("user_id"):
        try:
            user = await db.users.find_one(
                {"_id": ObjectId(order["user_id"])}
            )

            if user:
                user_email = user_email or user.get("email", "")
                customer_name = user.get("name", customer_name)

        except Exception as exc:
            print("ERROR BUSCANDO USUARIO:", exc)

    short_order_id = str(order_id)[-8:].upper()
    tracking_number = short_order_id

    shipping_data = order.get("shipping_address", {}) or {}

    if isinstance(shipping_data, dict):
        shipping_address = shipping_data.get(
            "full_address",
            order.get("shipping_address_text", "Dirección no disponible"),
        )
        recipient = shipping_data.get("recipient", customer_name)
        phone = shipping_data.get("phone", "No informado")
    else:
        shipping_address = str(shipping_data)
        recipient = customer_name
        phone = "No informado"

    subject = f"Actualización de tu pedido Ischuu #{short_order_id}"

    body = (
        f"Hola {customer_name},\n\n"
        "Te informamos que el estado de tu pedido ha sido actualizado.\n\n"
        f"Número de seguimiento: {tracking_number}\n"
        f"Fecha y hora de actualización: {updated_at_text}\n"
        f"Estado anterior: {old_status}\n"
        f"Estado actual: {new_status}\n\n"
        f"Dirección de despacho: {shipping_address}\n"
        f"Destinatario: {recipient}\n"
        f"Teléfono: {phone}\n\n"
        "Gracias por comprar en Ischuu."
    )

    html_body = f"""
    <html>
        <body style="margin:0; padding:0; background-color:#f4f4f5; font-family:Arial, Helvetica, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5; padding:30px 0;">
                <tr>
                    <td align="center">
                        <table width="620" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-collapse:collapse;">
                            <tr>
                                <td align="center" style="padding:24px 20px 12px;">
                                    <div style="font-size:26px; font-weight:800; letter-spacing:4px; color:#111111;">
                                        ISCHUU
                                    </div>
                                </td>
                            </tr>

                            <tr>
                                <td align="center" style="padding:0 30px 24px;">
                                    <div style="width:150px; height:1px; background-color:#111111;"></div>
                                </td>
                            </tr>

                            <tr>
                                <td align="center" style="padding:0 40px;">
                                    <h1 style="margin:0; font-size:26px; color:#111827;">
                                        Hola {customer_name},
                                    </h1>
                                </td>
                            </tr>

                            <tr>
                                <td align="center" style="padding:20px 55px;">
                                    <p style="margin:0; font-size:16px; color:#374151; line-height:1.6;">
                                        Te informamos que el estado de tu pedido ha sido actualizado.
                                    </p>
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:10px 55px 24px;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td width="50%" style="padding:0 20px 22px 0;">
                                                <div style="font-size:14px; font-weight:bold; color:#111827;">Número de seguimiento:</div>
                                                <div style="font-size:14px; color:#111827; margin-top:8px;">{tracking_number}</div>
                                            </td>

                                            <td width="50%" style="padding:0 0 22px 20px;">
                                                <div style="font-size:14px; font-weight:bold; color:#111827;">Fecha y hora:</div>
                                                <div style="font-size:14px; color:#111827; margin-top:8px;">{updated_at_text}</div>
                                            </td>
                                        </tr>

                                        <tr>
                                            <td width="50%" style="padding:0 20px 22px 0;">
                                                <div style="font-size:14px; font-weight:bold; color:#111827;">Estado anterior:</div>
                                                <div style="font-size:14px; color:#6b7280; margin-top:8px;">{old_status}</div>
                                            </td>

                                            <td width="50%" style="padding:0 0 22px 20px;">
                                                <div style="font-size:14px; font-weight:bold; color:#111827;">Estado actual:</div>
                                                <div style="font-size:14px; color:#ec4899; font-weight:bold; margin-top:8px;">{new_status}</div>
                                            </td>
                                        </tr>

                                        <tr>
                                            <td colspan="2" style="padding:0;">
                                                <div style="font-size:14px; font-weight:bold; color:#111827;">Dirección de despacho:</div>
                                                <div style="font-size:14px; color:#111827; line-height:1.7; margin-top:8px;">
                                                    {shipping_address}<br>
                                                    Destinatario: {recipient}<br>
                                                    Teléfono: {phone}
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:18px 36px; background-color:#111827; text-align:center;">
                                    <p style="margin:0; color:#d1d5db; font-size:12px;">
                                        Este correo fue enviado automáticamente por Ischuu. Por favor, no responder directamente.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """


    if user_email:
        email_sent = send_email(
            user_email,
            subject,
            body,
            html_body,
        )

        print("EMAIL SENT RESULT:", email_sent)
    else:
        print("NO SE ENVIÓ CORREO: user_email vacío.")

    updated_order = await db.orders.find_one(
        {"_id": oid(order_id)}
    )

    return serialize_order(updated_order)

def money_clp(value: int | float | str | None) -> str:
    try:
        number = int(value or 0)
    except Exception:
        number = 0

    return f"${number:,.0f}".replace(",", ".")

async def update_order_status(
    order_id: str,
    payload: dict,
    admin: dict = Depends(current_admin),
):
    new_status = str(payload.get("status", "")).strip()

    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido",
        )

    order = await db.orders.find_one(
        {"_id": oid(order_id)}
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    old_status = order.get("status", "Compra realizada")

    # Si el estado no cambió, no guardar historial ni enviar correo
    if old_status == new_status:
        return serialize_order(order)

    updated_at_iso = datetime.now(timezone.utc).isoformat()
    updated_at_text = format_datetime_chile()

    hist = {
        "from": old_status,
        "to": new_status,
        "changed_at": updated_at_iso,
        "changed_by": admin.get("email", "admin"),
    }

    await db.orders.update_one(
        {"_id": oid(order_id)},
        {
            "$set": {
                "status": new_status,
            },
            "$push": {
                "status_history": hist,
            },
        },
    )

    # Obtener correo del usuario dueño del pedido
    user_email = order.get("user_email", "")
    customer_name = order.get("user_name", "") or "Cliente"

    if (not user_email or customer_name == "Cliente") and order.get("user_id"):
        try:
            user = await db.users.find_one(
                {"_id": ObjectId(order["user_id"])}
            )

            if user:
                user_email = user_email or user.get("email", "")
                customer_name = user.get("name", customer_name)

        except Exception as exc:
            print("ERROR BUSCANDO USUARIO DEL PEDIDO:", exc)

    # Número de seguimiento: debe ser el mismo que aparece en el asunto
    short_order_id = str(order_id)[-8:].upper()
    tracking_number = short_order_id

    subject = f"Actualización de tu pedido Ischuu #{short_order_id}"

    # Dirección de despacho
    shipping_data = order.get("shipping_address", {}) or {}

    if isinstance(shipping_data, dict):
        shipping_address = shipping_data.get(
            "full_address",
            order.get("shipping_address_text", "Dirección no disponible"),
        )

        recipient = shipping_data.get("recipient", customer_name)
        phone = shipping_data.get("phone", "No informado")
        comuna = shipping_data.get("comuna", "")
        region = shipping_data.get("region", "")
    else:
        shipping_address = str(shipping_data)
        recipient = customer_name
        phone = "No informado"
        comuna = ""
        region = ""

    courier_name = order.get("courier_name", "Por confirmar")
    estimated_delivery = order.get("estimated_delivery", "Por confirmar")
    tracking_url = order.get("tracking_url", "")

    # Mensaje según estado
    if new_status == "Compra realizada":
        main_message = "Tu compra fue confirmada correctamente."
    elif new_status == "Artículo empaquetado":
        main_message = "Tu pedido ya fue preparado y está listo para despacho."
    elif new_status == "Artículo enviado":
        main_message = "Tu pedido ha sido enviado. Puedes revisar los detalles del despacho."
    elif new_status == "Artículo entregado":
        main_message = "Tu pedido fue entregado correctamente."
    else:
        main_message = "Tu pedido ha sido actualizado."

    # Artículos del pedido
    items = order.get("items", []) or []
    items_html = ""

    for item in items:
        item_name = item.get("name", "Producto")
        item_qty = int(item.get("quantity", 1))
        item_price = int(item.get("price", 0))
        item_subtotal = int(item.get("subtotal", item_price * item_qty))

        items_html += f"""
        <tr>
            <td style="padding:12px; border-bottom:1px solid #e5e7eb; color:#111827;">
                <strong>{item_name}</strong><br>
                <span style="font-size:12px; color:#6b7280;">Cantidad: x{item_qty}</span>
            </td>
            <td align="right" style="padding:12px; border-bottom:1px solid #e5e7eb; color:#111827;">
                {money_clp(item_subtotal)}
            </td>
        </tr>
        """

    if not items_html:
        items_html = """
        <tr>
            <td colspan="2" style="padding:12px; color:#6b7280;">
                Sin detalle de artículos.
            </td>
        </tr>
        """

    button_html = ""

    if tracking_url:
        button_html = f"""
        <tr>
            <td align="center" style="padding: 8px 30px 28px;">
                <a href="{tracking_url}"
                   style="
                       display:inline-block;
                       background-color:#f08f79;
                       color:#ffffff;
                       text-decoration:none;
                       padding:14px 30px;
                       font-size:16px;
                       font-weight:bold;
                       border-radius:4px;
                   ">
                    Seguir tu pedido &gt;
                </a>
            </td>
        </tr>
        """

    body = (
        f"Hola {customer_name},\n\n"
        f"{main_message}\n\n"
        f"Número de seguimiento: {tracking_number}\n"
        f"Fecha y hora de actualización: {updated_at_text}\n"
        f"Estado anterior: {old_status}\n"
        f"Estado actual: {new_status}\n\n"
        f"Dirección de despacho: {shipping_address}\n"
        f"Destinatario: {recipient}\n"
        f"Teléfono: {phone}\n\n"
        "Gracias por comprar en Ischuu."
    )

    html_body = f"""
    <html>
    <body style="margin:0; padding:0; background-color:#f4f4f5; font-family:Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5; padding:30px 0;">
            <tr>
                <td align="center">
                    <table width="620" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-collapse:collapse;">

                        <tr>
                            <td align="center" style="padding:22px 20px 12px;">
                                <div style="font-size:26px; font-weight:800; letter-spacing:4px; color:#111111;">
                                    ISCHUU
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding:0 30px 24px;">
                                <div style="width:150px; height:1px; background-color:#111111;"></div>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding:0 36px;">
                                <h1 style="margin:0; font-size:28px; color:#111827;">
                                    Hola {customer_name},
                                </h1>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding:20px 55px 16px;">
                                <p style="margin:0; font-size:16px; color:#111827; line-height:1.6;">
                                    {main_message}
                                </p>
                            </td>
                        </tr>

                        {button_html}

                        <tr>
                            <td style="padding:10px 55px 22px;">
                                <table width="100%" cellpadding="0" cellspacing="0">

                                    <tr>
                                        <td width="50%" valign="top" style="padding:0 20px 24px 0;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Número de pedido:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {order.get("buy_order", order_id)}
                                            </div>
                                        </td>

                                        <td width="50%" valign="top" style="padding:0 0 24px 20px;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Fecha y hora de actualización:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {updated_at_text}
                                            </div>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td width="50%" valign="top" style="padding:0 20px 24px 0;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Número de seguimiento:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {tracking_number}
                                            </div>
                                        </td>

                                        <td width="50%" valign="top" style="padding:0 0 24px 20px;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Empresa de transporte:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {courier_name}
                                            </div>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td width="50%" valign="top" style="padding:0 20px 24px 0;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Estado anterior:
                                            </div>
                                            <div style="font-size:14px; color:#6b7280;">
                                                {old_status}
                                            </div>
                                        </td>

                                        <td width="50%" valign="top" style="padding:0 0 24px 20px;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Estado actual:
                                            </div>
                                            <div style="font-size:14px; color:#ec4899; font-weight:bold;">
                                                {new_status}
                                            </div>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td width="50%" valign="top" style="padding:0 20px 24px 0;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Fecha de entrega estimada:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {estimated_delivery}
                                            </div>
                                        </td>

                                        <td width="50%" valign="top" style="padding:0 0 24px 20px;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Teléfono de contacto:
                                            </div>
                                            <div style="font-size:14px; color:#111827;">
                                                {phone}
                                            </div>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td colspan="2" valign="top" style="padding:0;">
                                            <div style="font-size:15px; font-weight:bold; color:#111827; margin-bottom:8px;">
                                                Dirección de despacho:
                                            </div>
                                            <div style="font-size:14px; color:#111827; line-height:1.8;">
                                                {shipping_address}<br>
                                                Destinatario: {recipient}<br>
                                                {comuna} {region}
                                            </div>
                                        </td>
                                    </tr>

                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:12px 36px 0;">
                                <div style="background-color:#000000; color:#ffffff; padding:14px 18px; font-size:16px; font-weight:bold;">
                                    Artículo(s) del pedido
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:0 36px 24px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb; border-top:none;">
                                    {items_html}
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:0 36px 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding:8px 0; color:#374151;">Subtotal</td>
                                        <td align="right" style="padding:8px 0; color:#111827;">
                                            {money_clp(order.get("subtotal", 0))}
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding:8px 0; color:#374151;">Envío</td>
                                        <td align="right" style="padding:8px 0; color:#111827;">
                                            {money_clp(order.get("shipping", 0))}
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding:8px 0; color:#374151;">Descuento</td>
                                        <td align="right" style="padding:8px 0; color:#111827;">
                                            -{money_clp(order.get("discount", 0))}
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding:12px 0; color:#111827; font-weight:bold; font-size:16px; border-top:1px solid #e5e7eb;">
                                            Total
                                        </td>
                                        <td align="right" style="padding:12px 0; color:#111827; font-weight:bold; font-size:16px; border-top:1px solid #e5e7eb;">
                                            {money_clp(order.get("total", 0))}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:18px 36px; background-color:#111827; text-align:center;">
                                <p style="margin:0; color:#d1d5db; font-size:12px;">
                                    Este correo fue enviado automáticamente por Ischuu. Por favor, no responder directamente.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """



    if user_email:
        email_sent = send_email(
            user_email,
            subject,
            body,
            html_body,
        )

        print("EMAIL SENT RESULT:", email_sent)
    else:
        print("NO SE ENVIÓ CORREO: user_email está vacío")

    updated_order = await db.orders.find_one(
        {"_id": oid(order_id)}
    )

    return serialize_order(updated_order)

@router.get("/settings")
async def get_settings(_: dict = Depends(current_admin)):
    doc = await db.settings.find_one({"key": "social"})
    if not doc:
        return {"instagram_url": "https://www.instagram.com/ischuu._", "tiktok_url": "https://www.tiktok.com/", "instagram_enabled": False, "tiktok_enabled": False}
    doc.pop("_id", None); doc.pop("key", None); return doc

@router.patch("/settings")
async def update_settings(payload: dict, _: dict = Depends(current_admin)):
    data = {"instagram_url": str(payload.get("instagram_url", "")), "tiktok_url": str(payload.get("tiktok_url", "")), "instagram_enabled": bool(payload.get("instagram_enabled", False)), "tiktok_enabled": bool(payload.get("tiktok_enabled", False)), "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.settings.update_one({"key": "social"}, {"$set": data}, upsert=True)
    return data
