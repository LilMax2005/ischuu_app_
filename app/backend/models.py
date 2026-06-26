"""Modelo documental y representaciones públicas de Ischuu.

MongoDB almacena documentos sin un ORM. Este módulo mantiene en un solo lugar
los nombres de colecciones, estados válidos y serializadores de salida.
"""

from __future__ import annotations


USERS_COLLECTION = "users"
PRODUCTS_COLLECTION = "products"
ORDERS_COLLECTION = "orders"
PAYMENTS_COLLECTION = "payments"

ORDER_STATUSES = ["Pagado", "Preparando", "En despacho", "Entregado", "Cancelado"]

LEGACY_ORDER_STATUSES = {
    "Compra realizada": "Pagado",
    "Artículo empaquetado": "Preparando",
    "Artículo enviado": "En despacho",
    "Artículo entregado": "Entregado",
}


def normalize_order_status(value: str | None) -> str:
    status = str(value or "Pagado").strip()
    return LEGACY_ORDER_STATUSES.get(status, status)


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "points": max(0, int(user.get("points", 0))),
        "preferences": user.get("preferences", {}) or {},
        "favorite_categories": user.get("favorite_categories", []),
        "preference_stats": user.get("preference_stats", {}) or {},
        "preferences_updated_at": user.get("preferences_updated_at", ""),
        "notifications_enabled": bool(user.get("notifications_enabled", True)),
        "is_admin": bool(user.get("is_admin", False)),
        "is_active": bool(user.get("is_active", True)),
        "shipping_address": user.get("shipping_address", {}) or {},
        "created_at": user.get("created_at", ""),
    }


def serialize_product(product: dict) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product.get("name", ""),
        "series": product.get("series", ""),
        "category": product.get("category", "General"),
        "rarity": product.get("rarity", "Común"),
        "price": max(0, int(product.get("price", 0))),
        "stock": max(0, int(product.get("stock", 0))),
        "is_original": bool(product.get("is_original", True)),
        "description": product.get("description", ""),
        "image_url": product.get("image_url", ""),
    }


def serialize_order(order: dict) -> dict:
    return {
        "id": str(order["_id"]),
        "user_id": order.get("user_id", ""),
        "created_at": order.get("created_at", ""),
        "items": order.get("items", []),
        "shipping_address": order.get("shipping_address", {}) or {},
        "shipping_address_text": order.get("shipping_address_text", ""),
        "user_email": order.get("user_email", ""),
        "user_name": order.get("user_name", ""),
        "subtotal": int(order.get("subtotal", 0)),
        "shipping": int(order.get("shipping", 0)),
        "discount": int(order.get("discount", 0)),
        "total": int(order.get("total", 0)),
        "status": normalize_order_status(order.get("status")),
        "payment_status": order.get("payment_status", ""),
        "payment_method": order.get("payment_method", "Webpay" if order.get("webpay_token") else ""),
        "points_earned": int(order.get("points_earned", 0)),
        "buy_order": order.get("buy_order", ""),
        "status_history": order.get("status_history", []) or [],
    }
