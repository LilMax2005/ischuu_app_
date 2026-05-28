from __future__ import annotations

from typing import Any

from app.frontend.models.entities import CartItem, Product


class AppState:
    def __init__(self) -> None:
        self.current_user: dict[str, Any] | None = None
        self.products: list[Product] = []
        self.cart: list[CartItem] = []
        self.orders: list[dict[str, Any]] = []
        self.search_text: str = ""
        self.category_filter: str = "Todas"

    @property
    def categories(self) -> list[str]:
        return ["Todas"] + sorted({product.category for product in self.products})

    @property
    def filtered_products(self) -> list[Product]:
        result = self.products

        if self.category_filter != "Todas":
            result = [
                product for product in result
                if product.category == self.category_filter
            ]

        query = self.search_text.lower().strip()
        if query:
            result = [
                product
                for product in result
                if query in product.name.lower()
                or query in product.series.lower()
                or query in product.category.lower()
                or query in product.description.lower()
            ]

        return result

    @property
    def cart_count(self) -> int:
        return sum(item.quantity for item in self.cart)

    @property
    def cart_total(self) -> int:
        return sum(item.product.price * item.quantity for item in self.cart)

    @property
    def shipping_total(self) -> int:
        if self.cart_total <= 0:
            return 0
        return 0 if self.cart_total >= 25000 else 3000

    @property
    def checkout_total(self) -> int:
        return self.cart_total + self.shipping_total
