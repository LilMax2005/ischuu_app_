from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


MIN_PRODUCTS_FOR_PREFERENCE = 2
MAX_FAVORITE_CATEGORIES = 3


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value

    text = str(value or "").strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _category_from_item(item: dict) -> str:
    category = str(item.get("category") or "General").strip()
    return category or "General"


def build_preference_profile(orders: list[dict]) -> dict:
    stats: dict[str, dict[str, Any]] = {}

    for order in orders:
        categories_in_order: set[str] = set()
        created_at = _parse_datetime(order.get("created_at"))

        for item in order.get("items", []) or []:
            category = _category_from_item(item)
            quantity = max(1, int(item.get("quantity", 1) or 1))
            subtotal = max(0, int(item.get("subtotal", 0) or 0))

            entry = stats.setdefault(
                category,
                {
                    "products_bought": 0,
                    "orders": 0,
                    "subtotal": 0,
                    "last_purchase_at": "",
                    "score": 0,
                },
            )
            entry["products_bought"] += quantity
            entry["subtotal"] += subtotal
            categories_in_order.add(category)

            if created_at is not None:
                previous = _parse_datetime(entry.get("last_purchase_at"))
                if previous is None or created_at > previous:
                    entry["last_purchase_at"] = created_at.isoformat()

        for category in categories_in_order:
            stats[category]["orders"] += 1

    for category, entry in stats.items():
        recency_bonus = 0
        last_purchase_at = _parse_datetime(entry.get("last_purchase_at"))
        if last_purchase_at is not None:
            days_since_purchase = (
                datetime.now(timezone.utc) - last_purchase_at.astimezone(timezone.utc)
            ).days
            if days_since_purchase <= 30:
                recency_bonus = 5
            elif days_since_purchase <= 90:
                recency_bonus = 2

        entry["score"] = (
            int(entry["products_bought"]) * 3
            + int(entry["orders"]) * 5
            + int(entry["subtotal"]) // 10_000
            + recency_bonus
        )

    ordered = sorted(
        stats.items(),
        key=lambda item: (
            int(item[1].get("score", 0)),
            int(item[1].get("products_bought", 0)),
            int(item[1].get("orders", 0)),
            str(item[0]),
        ),
        reverse=True,
    )

    favorite_categories = [
        category
        for category, entry in ordered
        if int(entry.get("products_bought", 0)) >= MIN_PRODUCTS_FOR_PREFERENCE
        or int(entry.get("orders", 0)) >= 2
    ][:MAX_FAVORITE_CATEGORIES]

    preferences = {
        category: int(entry.get("products_bought", 0))
        for category, entry in ordered
    }

    return {
        "preferences": preferences,
        "favorite_categories": favorite_categories,
        "preference_stats": {category: stats[category] for category, _ in ordered},
    }


async def refresh_user_preferences(database, user_id) -> dict:
    from bson import ObjectId

    object_id = user_id if isinstance(user_id, ObjectId) else ObjectId(str(user_id))
    orders = await database.orders.find(
        {"user_id": str(object_id), "payment_status": "paid"}
    ).to_list(length=5000)

    profile = build_preference_profile(orders)
    profile["preferences_updated_at"] = datetime.now(timezone.utc).isoformat()

    await database.users.update_one({"_id": object_id}, {"$set": profile})
    return profile
