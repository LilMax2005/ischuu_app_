from __future__ import annotations

from dataclasses import dataclass, field

from app.frontend.models.entities import CartItem, Product, User


@dataclass
class AppState:
    products: list[Product] = field(default_factory=list)
    cart: list[CartItem] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    current_user: User | None = None

    search_text: str = ""
    category_filter: str = "Todas"
    product_page: int = 1
    product_page_size: int = 10
    product_total: int = 0
    product_total_pages: int = 1
    product_categories: list[str] = field(default_factory=list)

    @property
    def categories(self) -> list[str]:
        if self.product_categories:
            categories = sorted(
                {
                    category
                    for category in self.product_categories
                    if category
                }
            )
        else:
            categories = sorted(
                {
                    product.category
                    for product in self.products
                    if getattr(product, "category", "")
                }
            )

        return ["Todas", *categories]

    @property
    def filtered_products(self) -> list[Product]:
        text = self.search_text.lower().strip()

        products = self.products

        if self.category_filter and self.category_filter != "Todas":
            products = [
                product
                for product in products
                if product.category == self.category_filter
            ]

        if text:
            products = [
                product
                for product in products
                if text in product.name.lower()
                or text in product.series.lower()
                or text in product.category.lower()
            ]

        return products

    @property
    def cart_count(self) -> int:
        return sum(item.quantity for item in self.cart)

    @property
    def cart_subtotal(self) -> int:
        return sum(
            int(item.product.price) * int(item.quantity)
            for item in self.cart
        )

    @property
    def shipping_cost(self) -> int:
        if self.cart_subtotal <= 0:
            return 0

        if self.cart_subtotal >= 25000:
            return 0

        return 3000

    @property
    def checkout_total(self) -> int:
        return self.cart_subtotal + self.shipping_cost
