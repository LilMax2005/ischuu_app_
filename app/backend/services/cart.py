from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException


def normalize_cart_items(items: list[dict]) -> list[dict]:
    if not items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    quantities: dict[str, int] = {}
    for item in items:
        product_id = str(item.get("product_id", "")).strip()
        quantity = int(item.get("quantity", 0))
        if not product_id or quantity <= 0:
            raise HTTPException(status_code=400, detail="Producto o cantidad inválida")
        quantities[product_id] = quantities.get(product_id, 0) + quantity

    return [
        {"product_id": product_id, "quantity": quantity}
        for product_id, quantity in quantities.items()
    ]


async def enrich_cart_items(database, items: list[dict]) -> list[dict]:
    normalized_items = normalize_cart_items(items)
    enriched_items: list[dict] = []

    for item in normalized_items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        try:
            object_id = ObjectId(product_id)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="ID de producto inválido") from exc

        product = await database.products.find_one({"_id": object_id})
        if product is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        stock = max(0, int(product.get("stock", 0)))
        if stock < quantity:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stock insuficiente para {product.get('name', 'el producto')}. "
                    f"Disponible: {stock}; solicitado: {quantity}."
                ),
            )

        price = int(product.get("price", 0))
        enriched_items.append(
            {
                "product_id": str(product["_id"]),
                "name": product.get("name", "Producto"),
                "category": product.get("category", "General"),
                "price": price,
                "quantity": quantity,
                "subtotal": price * quantity,
            }
        )

    return enriched_items
