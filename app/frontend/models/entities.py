from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


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


@dataclass
class Order:
    id: str
    created_at: str
    items: List[CartItem]
    total: int
    status: str = "Preparando"


@dataclass
class User:
    name: str
    email: str
    password: str
    points: int = 0
    notifications_enabled: bool = True
    favorite_categories: List[str] = field(default_factory=list)
