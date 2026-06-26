from __future__ import annotations

from fastapi import HTTPException


def normalize_shipping_address(data: dict) -> dict:
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Dirección de despacho requerida",
        )

    recipient = str(data.get("recipient", "")).strip()
    phone = str(data.get("phone", "")).strip()
    region = str(data.get("region", "")).strip()
    city = str(data.get("city", "")).strip()
    comuna = str(data.get("comuna", "")).strip()
    street = str(data.get("street", "")).strip()
    number = str(data.get("number", "")).strip()
    details = str(data.get("details", "")).strip()

    required_fields = {
        "Nombre destinatario": recipient,
        "Teléfono": phone,
        "Región": region,
        "Ciudad": city,
        "Comuna": comuna,
        "Calle": street,
        "Número": number,
    }

    missing = [
        name
        for name, value in required_fields.items()
        if not value
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan datos de despacho: {', '.join(missing)}",
        )

    if not phone.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El teléfono debe contener solamente números",
        )

    if not number.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El número de la dirección debe contener solamente números",
        )

    full_address = f"{street} {number}, {comuna}, {city}, {region}"

    if details:
        full_address = f"{full_address}. Referencia: {details}"

    return {
        "recipient": recipient,
        "phone": phone,
        "region": region,
        "city": city,
        "comuna": comuna,
        "street": street,
        "number": number,
        "details": details,
        "full_address": full_address,
    }
