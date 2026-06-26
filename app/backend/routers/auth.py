from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from app.backend.core.config import settings
from app.backend.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    get_user_by_email,
)
from app.backend.db import db
from app.backend.dependencies import get_current_active_user
from app.backend.models import serialize_user
from app.backend.schemas import (
    NotificationPreferenceUpdate,
    RefreshTokenPayload,
    ShippingAddressPayload,
    UserCreate,
)
from app.backend.services.shipping import normalize_shipping_address

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def auth_response(user: dict) -> dict:
    return {
        "access_token": create_access_token(
            subject=user["email"],
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        ),
        "refresh_token": create_refresh_token(subject=user["email"]),
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    if await get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    document = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": get_password_hash(payload.password),
        "points": 0,
        "preferences": {},
        "favorite_categories": [],
        "preference_stats": {},
        "notifications_enabled": True,
        "shipping_address": {},
        "is_admin": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = await db.users.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="El correo ya está registrado") from exc
    document["_id"] = result.inserted_id
    return serialize_user(document)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta a un administrador.",
        )

    return auth_response(user)


@router.post("/refresh")
async def refresh_session(payload: RefreshTokenPayload):
    user = await decode_refresh_token(payload.refresh_token)
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta a un administrador.",
        )
    return auth_response(user)


@router.get("/me")
async def me(user: dict = Depends(get_current_active_user)):
    return serialize_user(user)


@router.get("/me/points")
async def my_points(user: dict = Depends(get_current_active_user)):
    return {"points": max(0, int(user.get("points", 0)))}


@router.patch("/me/shipping-address")
async def update_my_shipping_address(
    payload: ShippingAddressPayload,
    user: dict = Depends(get_current_active_user),
):
    shipping_address = normalize_shipping_address(payload.model_dump())
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"shipping_address": shipping_address}},
    )
    updated_user = await db.users.find_one({"_id": user["_id"]})
    if updated_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(updated_user)


@router.patch("/me/notifications")
async def update_notification_preference(
    payload: NotificationPreferenceUpdate,
    user: dict = Depends(get_current_active_user),
):
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"notifications_enabled": payload.enabled}},
    )
    updated_user = await db.users.find_one({"_id": user["_id"]})
    if updated_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(updated_user)
