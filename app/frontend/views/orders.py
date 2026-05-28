from __future__ import annotations

from typing import List
import flet as ft

from app.models.entities import Order
from app.utils.formatters import currency


def build_orders_view(orders: List[Order]) -> ft.Control:
    cards: List[ft.Control] = [build_order_card(order) for order in orders]

    if not cards:
        cards = [
            ft.Container(
                padding=20,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Text("Aún no tienes pedidos registrados."),
            )
        ]

    return ft.Column(
        spacing=14,
        controls=[
            ft.Text("Seguimiento de pedidos", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(
                "El estado del pedido puede conectarse más adelante a un backend real con FastAPI + PostgreSQL o MongoDB.",
                color=ft.Colors.WHITE70,
            ),
            ft.Column(spacing=12, controls=cards),
        ],
    )


def build_order_card(order: Order) -> ft.Control:
    items_label = ", ".join([f"{item.product.name} x{item.quantity}" for item in order.items])

    return ft.Container(
        padding=16,
        border_radius=18,
        bgcolor="#1b1b1b",
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"Pedido #{order.id}", size=17, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            border_radius=999,
                            bgcolor="#1f7a1f",
                            content=ft.Text(order.status, size=12),
                        ),
                    ],
                ),
                ft.Text(f"Fecha: {order.created_at}", color=ft.Colors.WHITE70),
                ft.Text(items_label, color=ft.Colors.WHITE70),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Estado actual: En preparación / despacho"),
                        ft.Text(currency(order.total), weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.ProgressBar(value=0.55, border_radius=10),
            ],
        ),
    )
