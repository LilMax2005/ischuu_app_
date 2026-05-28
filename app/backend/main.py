from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.core.security import get_password_hash
from app.backend.db import db, ping_mongodb
from app.backend.routers import admin, auth, orders, payments, products
from app.backend.services.catalog import CATALOG


app = FastAPI(title="Ischuu API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup() -> None:
    if await db.users.count_documents({}) == 0:
        await db.users.insert_one(
            {
                "name": "Administrador Ischuu",
                "email": "admin@ischuu.cl",
                "password_hash": get_password_hash("Admin1234"),
                "points": 100,
                "preferences": {},
                "is_admin": True,
                "is_active": True,
            }
        )

    await db.users.update_one(
        {"email": "admin@ischuu.cl"},
        {
            "$set": {
                "is_admin": True,
                "is_active": True,
            }
        },
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