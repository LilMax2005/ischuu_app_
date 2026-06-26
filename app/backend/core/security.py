from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.backend.core.config import settings
from app.backend.db import db

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    return await db.users.find_one({"email": email.lower().strip()})


async def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    user = await get_user_by_email(email)
    if user is None:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


async def _decode_user_token(token: str, expected_type: str) -> dict[str, Any]:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        token_type = payload.get("type", "access")
        if not isinstance(email, str) or token_type != expected_type:
            raise exc
        user = await get_user_by_email(email)
        if user is None:
            raise exc
        return user
    except InvalidTokenError as err:
        raise exc from err


async def decode_token(token: str) -> dict[str, Any]:
    return await _decode_user_token(token, "access")


async def decode_refresh_token(token: str) -> dict[str, Any]:
    return await _decode_user_token(token, "refresh")
