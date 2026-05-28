from __future__ import annotations

FREE_SHIPPING_LIMIT = 25000
SHIPPING_COST = 3000

# Nueva lógica de puntos
POINT_EARN_EVERY_CLP = 500      # Cada $500 pagados = 1 punto
POINT_VALUE_CLP = 25            # 1 punto = $50 de descuento

# Puedes ajustar esto si quieres permitir usar desde 1 punto
MIN_POINTS_TO_REDEEM = 10       # mínimo 10 puntos para canjear = $500 descuento

# Protección para que el descuento no sea excesivo
MAX_POINTS_DISCOUNT_RATE = 0.20 # máximo 20% del subtotal

PREFERENCE_DISCOUNT_RATE = 0.05
MAX_PREFERENCE_DISCOUNT = 5000


def format_currency(value: int) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


def top_preference_categories(user: dict, limit: int = 3) -> list[str]:
    preferences = user.get("preferences", {}) or {}

    if not isinstance(preferences, dict):
        return []

    ordered = sorted(
        preferences.items(),
        key=lambda x: int(x[1]),
        reverse=True,
    )

    return [category for category, _ in ordered[:limit]]


def calculate_shipping(subtotal: int) -> int:
    if subtotal <= 0:
        return 0

    return 0 if subtotal >= FREE_SHIPPING_LIMIT else SHIPPING_COST


def calculate_preference_discount(
    enriched_items: list[dict],
    preferred_categories: set[str],
) -> int:
    preferred_subtotal = 0

    for item in enriched_items:
        if item.get("category") in preferred_categories:
            preferred_subtotal += int(item.get("subtotal", 0))

    discount = round(preferred_subtotal * PREFERENCE_DISCOUNT_RATE)

    return min(discount, MAX_PREFERENCE_DISCOUNT)


def calculate_points_discount(
    subtotal: int,
    preference_discount: int,
    user_points: int,
    use_points: bool = False,
    requested_points: int | None = None,
) -> dict:
    if not use_points:
        return {
            "points_to_spend": 0,
            "points_discount": 0,
            "points_discount_label": "No se utilizaron puntos",
        }

    if user_points < MIN_POINTS_TO_REDEEM:
        return {
            "points_to_spend": 0,
            "points_discount": 0,
            "points_discount_label": f"Necesitas al menos {MIN_POINTS_TO_REDEEM} puntos para canjear",
        }

    discount_base = max(0, subtotal - preference_discount)

    max_discount_by_rule = round(subtotal * MAX_POINTS_DISCOUNT_RATE)
    max_discount_by_total = discount_base

    max_points_by_rule = max_discount_by_rule // POINT_VALUE_CLP
    max_points_by_total = max_discount_by_total // POINT_VALUE_CLP

    max_usable_points = min(
        user_points,
        max_points_by_rule,
        max_points_by_total,
    )

    if requested_points is not None:
        max_usable_points = min(
            max_usable_points,
            max(0, int(requested_points)),
        )

    if max_usable_points < MIN_POINTS_TO_REDEEM:
        return {
            "points_to_spend": 0,
            "points_discount": 0,
            "points_discount_label": f"Necesitas al menos {MIN_POINTS_TO_REDEEM} puntos para canjear",
        }

    points_discount = max_usable_points * POINT_VALUE_CLP

    return {
        "points_to_spend": max_usable_points,
        "points_discount": points_discount,
        "points_discount_label": f"Usaste {max_usable_points} puntos por {format_currency(points_discount)} de descuento",
    }


def earned_points_for_amount(product_amount_paid: int) -> int:
    """
    Cada $500 pagados en productos genera 1 punto.
    El envío no genera puntos.
    """
    if product_amount_paid <= 0:
        return 0

    return product_amount_paid // POINT_EARN_EVERY_CLP


def calculate_cart_totals(
    enriched_items: list[dict],
    user: dict,
    use_points: bool = False,
    requested_points: int | None = None,
) -> dict:
    subtotal = sum(int(item["subtotal"]) for item in enriched_items)

    user_points = int(user.get("points", 0))
    preferred_categories = set(top_preference_categories(user))

    preference_discount = calculate_preference_discount(
        enriched_items,
        preferred_categories,
    )

    points_data = calculate_points_discount(
        subtotal=subtotal,
        preference_discount=preference_discount,
        user_points=user_points,
        use_points=use_points,
        requested_points=requested_points,
    )

    points_discount = int(points_data["points_discount"])
    points_to_spend = int(points_data["points_to_spend"])

    shipping = calculate_shipping(subtotal)

    total_discount = preference_discount + points_discount

    product_amount_paid = max(
        0,
        subtotal - total_discount,
    )

    total = product_amount_paid + shipping

    points_earned_estimated = earned_points_for_amount(product_amount_paid)

    return {
        "subtotal": subtotal,
        "shipping": shipping,
        "preference_discount": preference_discount,
        "points_discount": points_discount,
        "points_to_spend": points_to_spend,
        "points_discount_label": points_data["points_discount_label"],
        "total_discount": total_discount,
        "total": total,
        "product_amount_paid": product_amount_paid,
        "points_earned_estimated": points_earned_estimated,
        "preferred_categories": list(preferred_categories),
        "available_points": user_points,
        "point_value_clp": POINT_VALUE_CLP,
        "point_earn_every_clp": POINT_EARN_EVERY_CLP,
        "min_points_to_redeem": MIN_POINTS_TO_REDEEM,
        "max_points_discount_rate": MAX_POINTS_DISCOUNT_RATE,
    }