from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.backend.core.security import decode_token


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    return await decode_token(bearer_token(authorization))


async def get_current_active_user(
    user: dict = Depends(get_current_user),
) -> dict:
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta a un administrador.",
        )
    return user


async def get_current_admin(
    user: dict = Depends(get_current_active_user),
) -> dict:
    if not bool(user.get("is_admin", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return user
