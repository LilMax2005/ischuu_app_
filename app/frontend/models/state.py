from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from app.data.seed import DEFAULT_USERS, PRODUCTS
from app.models.entities import CartItem, Order, Product, User


class AppState:
    def __init__(self) -> None:
        self.users: dict[str, User] = DEFAULT_USERS.copy()
        self.current_user: Optional[User] = None
        self.products: list[Product] = PRODUCTS.copy()
        self.cart: list[CartItem] = []
        self.orders: list[Order] = []
        self.search_text: str = ""
        self.category_filter: str = "Todas"

    @property
    def categories(self) -> list[str]:
        return ["Todas"] + sorted({product.category for product in self.products})

    @property
    def filtered_products(self) -> list[Product]:
        result = self.products

        if self.category_filter != "Todas":
            result = [product for product in result if product.category == self.category_filter]

        query = self.search_text.lower().strip()
        if query:
            result = [
                product
                for product in result
                if query in product.name.lower()
                or query in product.series.lower()
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
        if self.cart_total == 0:
            return 0
        if self.cart_total > 25000:
            return 0
        return 3990

    @property
    def checkout_total(self) -> int:
        return self.cart_total + self.shipping_total

    def login(self, email: str, password: str) -> bool:
        normalized = email.lower().strip()
        user = self.users.get(normalized)
        if not user or user.password != password:
            return False
        self.current_user = user
        return True

    def register(self, name: str, email: str, password: str) -> tuple[bool, str]:
        normalized = email.lower().strip()
        if normalized in self.users:
            return False, "Este correo ya está registrado."

        self.users[normalized] = User(
            name=name.strip(),
            email=normalized,
            password=password,
        )
        return True, "Cuenta creada correctamente."

    def logout(self) -> None:
        self.current_user = None
        self.cart.clear()
        self.search_text = ""
        self.category_filter = "Todas"

    def add_to_cart(self, product_id: str) -> None:
        product = next((product for product in self.products if product.id == product_id), None)
        if not product:
            raise ValueError("Producto no encontrado")
        if product.stock <= 0:
            raise ValueError("Producto sin stock")

        current_item = next((item for item in self.cart if item.product.id == product_id), None)
        if current_item:
            if current_item.quantity >= product.stock:
                raise ValueError("No puedes agregar más unidades que el stock disponible")
            current_item.quantity += 1
            return

        self.cart.append(CartItem(product=product, quantity=1))

    def change_quantity(self, product_id: str, delta: int) -> None:
        item = next((cart_item for cart_item in self.cart if cart_item.product.id == product_id), None)
        if not item:
            return

        new_quantity = item.quantity + delta
        if new_quantity <= 0:
            self.cart = [cart_item for cart_item in self.cart if cart_item.product.id != product_id]
            return

        if new_quantity > item.product.stock:
            raise ValueError("Cantidad superior al stock disponible")

        item.quantity = new_quantity

    def place_order(self) -> Order:
        if not self.current_user:
            raise PermissionError("Debes iniciar sesión")
        if not self.cart:
            raise ValueError("Tu carrito está vacío")

        order = Order(
            id=str(uuid.uuid4())[:8].upper(),
            created_at=datetime.now().strftime("%d-%m-%Y %H:%M"),
            items=[CartItem(item.product, item.quantity) for item in self.cart],
            total=self.checkout_total,
            status="Pagado",
        )

        self.orders.insert(0, order)

        for item in self.cart:
            original_product = next((product for product in self.products if product.id == item.product.id), None)
            if original_product:
                original_product.stock -= item.quantity

        self.current_user.points += max(10, order.total // 1000)
        self.cart.clear()
        return order
