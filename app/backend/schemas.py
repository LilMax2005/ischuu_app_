from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserRead(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False
    points: int = 0
    created_at: datetime


class ProductCreate(BaseModel):
    name: str
    series: str
    description: str
    category: str
    rarity: str
    image_url: Optional[str] = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    is_original: bool = True


class ProductRead(BaseModel):
    id: str
    name: str
    series: str
    description: str
    category: str
    rarity: str
    image_url: Optional[str] = None
    price: float
    stock: int
    is_original: bool = True
    is_active: bool = True
    created_at: datetime


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, le=20)


class OrderItemRead(BaseModel):
    id: str
    product_id: str
    quantity: int
    unit_price: float


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderRead(BaseModel):
    id: str
    user_id: str
    status: str
    payment_status: str
    total: float
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    items: list[OrderItemRead]


class PaymentIntentRequest(BaseModel):
    order_id: str


class PaymentIntentResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
