from __future__ import annotations

from datetime import datetime
from typing import Any

import flet as ft

from app.frontend.utils.formatters import currency
from app.frontend.views.components import build_summary_row
from app.frontend.views.theme import (
    IschuuColors,
    card,
    muted_text,
    section_title,
    status_pill,
)


ORDER_STEPS = [
    "Pagado",
    "Preparando",
    "En despacho",
    "Entregado",
]

LEGACY_STATUSES = {
    "Compra realizada": "Pagado",
    "Artículo empaquetado": "Preparando",
    "Artículo enviado": "En despacho",
    "Artículo entregado": "Entregado",
}


def order_get(order: Any, key: str, default=None):
    if isinstance(order, dict):
        return order.get(key, default)

    return getattr(order, key, default)


def format_order_date(value: str) -> str:
    if not value:
        return "Fecha no disponible"

    try:
        clean_value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_value)

        try:
            from zoneinfo import ZoneInfo

            dt = dt.astimezone(ZoneInfo("America/Santiago"))
        except Exception:
            pass

        return dt.strftime("%d/%m/%Y %H:%M hrs")

    except Exception:
        return value


def normalize_status(status: str) -> str:
    status = str(status or "").strip()

    if status.lower() in ["pagado", "paid", "authorized"]:
        return "Pagado"

    status = LEGACY_STATUSES.get(status, status)

    if status not in [*ORDER_STEPS, "Cancelado"]:
        return "Pagado"

    return status


def payment_label(payment_status: str) -> str:
    value = str(payment_status or "").lower().strip()

    if value in ["paid", "authorized", "pagado"]:
        return "Pagado"

    if value in ["failed", "rejected"]:
        return "Rechazado"

    if value in ["created", "pending", "pendiente"]:
        return "Pendiente"

    return payment_status or "Sin estado"


def build_orders_view(controller) -> ft.Control:
    orders = getattr(controller.state, "orders", []) or []

    if not orders:
        return ft.Column(
            spacing=14,
            controls=[
                section_title("Seguimiento de pedidos", 22),
                muted_text("Los pedidos aparecen aquí solo después de un pago autorizado."),
                card(
                    muted_text("Aún no tienes pedidos registrados."),
                    padding=20,
                ),
            ],
        )

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Seguimiento de pedidos", 22),
            muted_text("Los pedidos aparecen aquí solo después de un pago autorizado."),
            ft.Column(
                spacing=12,
                controls=[
                    build_order_card(order)
                    for order in orders
                ],
            ),
        ],
    )


def build_order_card(order: Any) -> ft.Control:
    order_id = str(order_get(order, "id", ""))

    created_at = format_order_date(
        str(order_get(order, "created_at", ""))
    )

    raw_status = order_get(order, "status", "Pagado")
    tracking_status = normalize_status(raw_status)

    payment_status = payment_label(
        str(order_get(order, "payment_status", ""))
    )

    items = order_get(order, "items", []) or []

    items_text = ", ".join(
        [
            f"{item.get('name', 'Producto')} x{item.get('quantity', 1)}"
            for item in items
        ]
    )

    # Dirección de despacho
    shipping_address = order_get(order, "shipping_address", {}) or {}

    if isinstance(shipping_address, dict):
        shipping_address_text = shipping_address.get(
            "full_address",
            order_get(
                order,
                "shipping_address_text",
                "Dirección no disponible",
            ),
        )

        recipient = shipping_address.get(
            "recipient",
            "No informado",
        )

        phone = shipping_address.get(
            "phone",
            "No informado",
        )
    else:
        shipping_address_text = str(
            shipping_address
            or order_get(
                order,
                "shipping_address_text",
                "Dirección no disponible",
            )
        )

        recipient = "No informado"
        phone = "No informado"

    subtotal = int(order_get(order, "subtotal", 0))
    shipping = int(order_get(order, "shipping", 0))
    discount = int(order_get(order, "discount", 0))
    total = int(order_get(order, "total", 0))
    points_earned = int(order_get(order, "points_earned", 0))

    is_cancelled = tracking_status == "Cancelado"
    current_step_index = -1 if is_cancelled else ORDER_STEPS.index(tracking_status)
    progress_value = 0 if is_cancelled else (current_step_index + 1) / len(ORDER_STEPS)

    return card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    f"Pedido #{order_id}",
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=IschuuColors.TEXT,
                                ),
                                ft.Text(
                                    f"Fecha: {created_at}",
                                    color=IschuuColors.TEXT_MUTED,
                                    size=13,
                                ),
                            ],
                        ),
                        status_pill(payment_status, "success"),
                    ],
                ),

                ft.Container(
                    padding=12,
                    border_radius=14,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.LOCAL_SHIPPING_OUTLINED,
                                        color=IschuuColors.PRIMARY,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Estado del pedido",
                                        color=IschuuColors.TEXT,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Text(
                                tracking_status,
                                color=IschuuColors.VANILLA,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.ProgressBar(
                                value=progress_value,
                                color=IschuuColors.PRIMARY_STRONG,
                                bgcolor=IschuuColors.BORDER,
                                border_radius=10,
                            ),
                            ft.Row(
                                wrap=True,
                                spacing=8,
                                run_spacing=8,
                                controls=[
                                    build_step_chip(
                                        step,
                                        index <= current_step_index,
                                    )
                                    for index, step in enumerate(ORDER_STEPS)
                                ],
                            ),
                        ],
                    ),
                ),

                ft.Container(
                    padding=12,
                    border_radius=14,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.LOCATION_ON_OUTLINED,
                                        color=IschuuColors.PRIMARY,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Dirección de despacho",
                                        color=IschuuColors.TEXT,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Text(
                                shipping_address_text,
                                color=IschuuColors.TEXT_MUTED,
                                size=13,
                            ),
                            ft.Text(
                                f"Recibe: {recipient} · Tel: {phone}",
                                color=IschuuColors.TEXT_MUTED,
                                size=12,
                            ),
                        ],
                    ),
                ),

                ft.Text(
                    items_text or "Sin detalle de productos",
                    color=IschuuColors.TEXT_MUTED,
                    size=14,
                ),

                build_summary_row("Subtotal", currency(subtotal)),
                build_summary_row("Envío", currency(shipping)),
                build_summary_row("Descuento", f"-{currency(discount)}"),
                build_summary_row("Total", currency(total), highlight=True),
                build_summary_row("Puntos ganados", str(points_earned)),

                ft.Divider(color=IschuuColors.PRIMARY_STRONG),
            ],
        ),
        padding=16,
    )


def build_step_chip(label: str, active: bool) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        bgcolor=IschuuColors.PRIMARY_STRONG if active else IschuuColors.SURFACE_ALT,
        content=ft.Text(
            label,
            size=11,
            weight=ft.FontWeight.W_600,
            color=IschuuColors.TEXT if active else IschuuColors.TEXT_MUTED,
        ),
    )
