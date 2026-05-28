from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from app.frontend.utils.formatters import currency
from app.frontend.views.theme import (
    IschuuColors,
    card,
    muted_text,
    section_title,
    status_pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_orders_view(controller: "AppController") -> ft.Control:
    if not controller.state.current_user:
        return card(
            ft.Column(
                spacing=10,
                controls=[
                    section_title("Pedidos", 22),
                    muted_text("Inicia sesión para revisar el seguimiento de tus compras."),
                ],
            )
        )

    cards = [build_order_card(order) for order in controller.state.orders]

    if not cards:
        cards = [
            card(
                ft.Text("Aún no tienes pedidos pagados.", color=IschuuColors.TEXT_MUTED),
                padding=20,
            )
        ]

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Seguimiento de pedidos", 22),
            muted_text("Los pedidos aparecen aquí solo después de un pago autorizado."),
            ft.Column(spacing=12, controls=cards),
        ],
    )


def build_order_card(order: dict[str, Any]) -> ft.Control:
    item_names = []
    for item in order.get("items", []):
        item_names.append(f"{item.get('name', 'Producto')} x{item.get('quantity', 1)}")

    items_label = ", ".join(item_names) if item_names else "Sin detalle"

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"Pedido #{order.get('id')}", size=17, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                        status_pill(order.get("status", "Pagado"), "success"),
                    ],
                ),
                ft.Text(f"Fecha: {order.get('created_at', '-')}", color=IschuuColors.TEXT_MUTED),
                ft.Text(items_label, color=IschuuColors.TEXT_MUTED),
                build_order_amounts(order),
                ft.ProgressBar(
                    value=1.0 if order.get("payment_status") == "paid" else 0.35,
                    border_radius=10,
                    color=IschuuColors.PRIMARY_STRONG,
                    bgcolor=IschuuColors.SURFACE_ALT,
                ),
            ],
        ),
        padding=16,
    )


def build_order_amounts(order: dict[str, Any]) -> ft.Control:
    return ft.Column(
        spacing=4,
        controls=[
            amount_row("Subtotal", currency(int(order.get("subtotal", 0)))),
            amount_row("Envío", currency(int(order.get("shipping", 0)))),
            amount_row("Descuento", f"-{currency(int(order.get('discount', 0)))}"),
            amount_row("Total", currency(int(order.get("total", 0))), True),
            amount_row("Puntos ganados", str(order.get("points_earned", 0))),
        ],
    )


def amount_row(label: str, value: str, highlight: bool = False) -> ft.Control:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(label, color=IschuuColors.TEXT if highlight else IschuuColors.TEXT_MUTED),
            ft.Text(value, weight=ft.FontWeight.BOLD, color=IschuuColors.VANILLA if highlight else IschuuColors.TEXT),
        ],
    )
