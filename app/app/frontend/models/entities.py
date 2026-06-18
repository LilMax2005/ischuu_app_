from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    id: str
    name: str
    series: str
    price: int
    stock: int
    category: str
    rarity: str
    description: str
    is_original: bool
    image: str = ""


@dataclass
class CartItem:
    product: Product
    quantity: int = 1
from dataclasses import dataclass, field


@dataclass
class User:
    id: str
    name: str
    email: str
    points: int = 0
    favorite_categories: list[str] = field(default_factory=list)
    notifications_enabled: bool = True
    is_admin: bool = False
    is_active: bool = True
    shipping_address: dict = field(default_factory=dict)