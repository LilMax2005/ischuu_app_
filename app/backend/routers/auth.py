from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.backend.core.config import settings
from app.backend.core.security import (
    authenticate_user,
    create_access_token,
    decode_token,
    get_password_hash,
    get_user_by_email,
)
from app.backend.db import db
from app.backend.services.shipping import normalize_shipping_address

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "points": int(user.get("points", 0)),
        "preferences": user.get("preferences", {}) or {},
        "favorite_categories": user.get("favorite_categories", []),
        "notifications_enabled": bool(user.get("notifications_enabled", True)),
        "is_admin": bool(user.get("is_admin", False)),
        "is_active": bool(user.get("is_active", True)),
        "shipping_address": user.get("shipping_address", {}) or {},
    }


async def current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token requerido",
        )

    return await decode_token(
        authorization.replace("Bearer ", "").strip()
    )


@router.post("/register")
async def register(payload: dict):
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).lower().strip()
    password = str(payload.get("password", "")).strip()

    if not name or not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Nombre, correo y contraseña son obligatorios",
        )

    if await get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado",
        )

    doc = {
        "name": name,
        "email": email,
        "password_hash": get_password_hash(password),
        "points": 0,
        "preferences": {},
        "favorite_categories": [],
        "notifications_enabled": True,
        "shipping_address": {},
        "is_admin": False,
        "is_active": True,
    }

    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    return serialize_user(doc)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await authenticate_user(
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user["email"],
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes,
        ),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
async def me(
    user: dict = Depends(current_user),
):
    return serialize_user(user)


@router.patch("/me/shipping-address")
async def update_my_shipping_address(
    payload: dict,
    user: dict = Depends(current_user),
):
    shipping_address = normalize_shipping_address(payload)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "shipping_address": shipping_address,
            }
        },
    )

    updated_user = await db.users.find_one(
        {"_id": user["_id"]}
    )

    if updated_user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    return serialize_user(updated_user)