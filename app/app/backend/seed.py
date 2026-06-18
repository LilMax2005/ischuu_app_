"""Carga manual del catálogo de demostración.

Uso: python -m app.backend.seed
El administrador inicial se configura con ADMIN_EMAIL y ADMIN_PASSWORD al
iniciar la API; este script no crea cuentas ni contiene contraseñas.
"""

from __future__ import annotations

import asyncio

from app.backend.db import db
from app.backend.services.catalog import CATALOG


async def seed() -> None:
    for payload in CATALOG:
        await db.products.update_one(
            {"name": payload["name"]},
            {"$setOnInsert": payload},
            upsert=True,
        )
    print(f"Catálogo verificado: {len(CATALOG)} productos")


if __name__ == "__main__":
    asyncio.run(seed())
