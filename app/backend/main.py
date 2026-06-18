from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.core.config import settings
from app.backend.core.security import get_password_hash
from app.backend.db import db, ping_mongodb
from app.backend.routers import admin, auth, notifications, orders, password, payments, products
from app.backend.services.catalog import CATALOG

app = FastAPI(title="Ischuu API", version="2.0.0")

allowed_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path("app/backend/static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(notifications.router)

app.include_router(password.router)


@app.on_event("startup")
async def startup() -> None:
    await db.users.create_index("email", unique=True)
    await db.payments.create_index("token", unique=True, sparse=True)
    await db.orders.create_index("webpay_token", unique=True, sparse=True)

    admin_email = settings.admin_email.lower().strip()
    admin_password = settings.admin_password.strip()
    if admin_email and admin_password:
        admin_user = await db.users.find_one({"email": admin_email})
        if admin_user is None:
            await db.users.insert_one(
                {
                    "name": "Administrador Ischuu",
                    "email": admin_email,
                    "password_hash": get_password_hash(admin_password),
                    "points": 0,
                    "preferences": {},
                    "favorite_categories": [],
                    "notifications_enabled": True,
                    "shipping_address": {},
                    "is_admin": True,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            await db.users.update_one(
                {"_id": admin_user["_id"]},
                {"$set": {"is_admin": True, "is_active": True}},
            )

    if await db.products.count_documents({}) == 0:
        await db.products.insert_many(CATALOG)


@app.get("/")
async def root():
    return {
        "app": "Ischuu API",
        "mongodb": "ok" if await ping_mongodb() else "error",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"ok": True}
