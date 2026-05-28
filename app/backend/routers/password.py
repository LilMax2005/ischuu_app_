from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.backend.core.security import get_password_hash
from app.backend.db import db
from app.backend.services.email import send_email

router = APIRouter(prefix="/api/v1/password", tags=["Password Recovery"])


@router.post("/forgot")
async def forgot_password(payload: dict):
    email = str(payload.get("email", "")).lower().strip()

    if not email:
        raise HTTPException(status_code=400, detail="Correo requerido")

    user = await db.users.find_one({"email": email})

    # No revelamos si el usuario existe o no.
    if user is None:
        return {
            "message": "Si el correo existe, se enviarán instrucciones de recuperación."
        }

    token = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    await db.password_resets.insert_one(
        {
            "email": email,
            "token": token,
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
        }
    )

    body = (
        "Hola,\n\n"
        "Recibimos una solicitud para recuperar tu contraseña de Ischuu.\n\n"
        f"Token de recuperación:\n{token}\n\n"
        "Este token vence en 30 minutos.\n\n"
        "Si no solicitaste este cambio, ignora este correo."
    )

    send_email(
        email,
        "Recuperación de contraseña Ischuu",
        body,
    )

    return {
        "message": "Si el correo existe, se enviarán instrucciones de recuperación.",
        "dev_token": token,
    }


@router.post("/reset")
async def reset_password(payload: dict):
    token = str(payload.get("token", "")).strip()
    new_password = str(payload.get("new_password", "")).strip()

    if not token or not new_password:
        raise HTTPException(
            status_code=400,
            detail="Token y nueva contraseña son obligatorios",
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 6 caracteres",
        )

    reset = await db.password_resets.find_one(
        {
            "token": token,
            "used": False,
        }
    )

    if reset is None:
        raise HTTPException(
            status_code=400,
            detail="Token inválido o utilizado",
        )

    expires_at = datetime.fromisoformat(reset["expires_at"])

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=400,
            detail="Token expirado",
        )

    email = reset["email"]

    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "password_hash": get_password_hash(new_password),
            }
        },
    )

    await db.password_resets.update_one(
        {"token": token},
        {
            "$set": {
                "used": True,
                "used_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    return {
        "message": "Contraseña actualizada correctamente",
    }