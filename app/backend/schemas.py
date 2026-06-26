from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def clean_email(value: str) -> str:
    email = str(value).lower().strip()
    local, separator, domain = email.partition("@")
    if not separator or not local or "." not in domain:
        raise ValueError("Correo inválido")
    return email


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return clean_email(value)


class ShippingAddressPayload(BaseModel):
    recipient: str
    phone: str
    region: str
    comuna: str
    street: str
    number: str
    details: str = ""


class NotificationPreferenceUpdate(BaseModel):
    enabled: bool


class RefreshTokenPayload(BaseModel):
    refresh_token: str = Field(min_length=20)


class CartItemPayload(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=100)


class CartQuoteRequest(BaseModel):
    items: list[CartItemPayload]
    use_points: bool = False
    requested_points: int | None = Field(default=None, ge=0)


class CartPaymentRequest(CartQuoteRequest):
    shipping_address: ShippingAddressPayload


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    points: int | None = Field(default=None, ge=0)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    series: str = ""
    category: str = Field(min_length=1, max_length=80)
    rarity: str = "Común"
    price: int = Field(gt=0)
    stock: int = Field(ge=0)
    is_original: bool = True
    description: str = ""
    image_url: str = ""

    @field_validator("name", "category", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return str(value).strip()


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    series: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    rarity: str | None = None
    price: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_original: bool | None = None
    description: str | None = None
    image_url: str | None = None

    @field_validator("name", "category", mode="before")
    @classmethod
    def normalize_optional_required_text(cls, value: str | None) -> str | None:
        return None if value is None else str(value).strip()


class StockUpdate(BaseModel):
    operation: Literal["add", "set"]
    quantity: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)


class OrderStatusUpdate(BaseModel):
    status: str


class SocialSettingsUpdate(BaseModel):
    instagram_url: str = ""
    tiktok_url: str = ""
    instagram_enabled: bool = False
    tiktok_enabled: bool = False


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return clean_email(value)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)
