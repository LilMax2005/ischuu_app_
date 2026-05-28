from __future__ import annotations

from typing import TYPE_CHECKING, List
import flet as ft

from app.models.entities import CartItem
from app.utils.formatters import currency
from app.views.components import build_summary_row

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


def build_cart_view(controller: "AppController") -> ft.Control:
    items_controls: List[ft.Control] = [build_cart_item(controller, item) for item in controller.state.cart]

    if not items_controls:
        items_controls = [
            ft.Container(
                padding=20,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Column(
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.REMOVE_SHOPPING_CART_OUTLINED, size=48),
                        ft.Text("Tu carrito está vacío."),
                    ],
                ),
            )
        ]

    return ft.Column(
        spacing=14,
        controls=[
            ft.Text("Carrito", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(
                "En una versión productiva aquí se integraría Stripe o PayPal mediante backend FastAPI.",
                color=ft.Colors.WHITE70,
            ),
            ft.Column(spacing=12, controls=items_controls),
            ft.Container(
                padding=16,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Column(
                    spacing=10,
                    controls=[
                        build_summary_row("Productos", str(controller.state.cart_count)),
                        build_summary_row("Subtotal", currency(controller.state.cart_total)),
                        build_summary_row("Envío", currency(controller.state.shipping_total)),
                        ft.Divider(color="#ffffff12"),
                        build_summary_row("Total", currency(controller.state.checkout_total), highlight=True),
                        ft.FilledButton(
                            content="Pagar ahora",
                            icon=ft.Icons.PAYMENTS,
                            height=48,
                            on_click=controller.handle_checkout,
                            disabled=not controller.state.cart,
                        ),
                    ],
                ),
            ),
        ],
    )


def build_cart_item(controller: "AppController", item: CartItem) -> ft.Control:
    def increase(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, 1)

    def decrease(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, -1)

    return ft.Container(
        padding=14,
        border_radius=18,
        bgcolor="#1b1b1b",
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    border_radius=12,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(
                        src=item.product.image,
                        width=90,
                        height=90,
                        fit=ft.BoxFit.COVER,
                        border_radius=12,
                    ),
                ),
                ft.Column(
                    expand=True,
                    spacing=6,
                    controls=[
                        ft.Text(item.product.name, weight=ft.FontWeight.BOLD),
                        ft.Text(currency(item.product.price), color=ft.Colors.WHITE70),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=decrease),
                                ft.Text(str(item.quantity), size=16, weight=ft.FontWeight.BOLD),
                                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=increase),
                            ],
                        ),
                    ],
                ),
                ft.Text(currency(item.product.price * item.quantity), weight=ft.FontWeight.BOLD),
            ],
        ),
    )
