from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.models.entities import CartItem
from app.frontend.utils.formatters import currency
from app.frontend.views.components import build_summary_row
from app.frontend.views.theme import (
    IschuuColors,
    card,
    image_box,
    muted_text,
    outline_button_style,
    primary_button_style,
    section_title,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_cart_view(controller: "AppController") -> ft.Control:
    items_controls = [build_cart_item(controller, item) for item in controller.state.cart]

    cart_quote = getattr(controller, "cart_quote", {}) or {}

    total_to_pay = int(
        cart_quote.get(
            "total",
            controller.state.checkout_total,
        )
    )

    has_backend_quote = bool(cart_quote)

    if not items_controls:
        items_controls = [
            card(
                ft.Column(
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.REMOVE_SHOPPING_CART_OUTLINED, size=48, color=IschuuColors.TEXT_SOFT),
                        muted_text("Tu carrito está vacío."),
                    ],
                ),
                padding=20,
            )
        ]

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Carrito", 22),
            muted_text("Revisa tus productos, envío, descuentos y total antes de abrir Webpay."),
            ft.Column(spacing=12, controls=items_controls),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        build_summary_row("Productos", str(controller.state.cart_count)),
                        build_summary_row("Subtotal", currency(controller.state.cart_total)),
                        build_summary_row("Envío", "Gratis" if controller.state.shipping_total == 0 and controller.state.cart_total else currency(controller.state.shipping_total)),
                        ft.Text("Envío gratis desde $25.000.", color=IschuuColors.SUCCESS, size=12, weight=ft.FontWeight.W_600),
                        ft.Divider(color=IschuuColors.BORDER),
                        controller.use_points_switch,
                        controller.cart_quote_box,
                        ft.OutlinedButton(
                            content="Actualizar descuentos",
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: controller.run_async(controller.refresh_cart_quote()),
                            disabled=not controller.state.cart or not controller.state.current_user,
                            style=outline_button_style(),
                        ),

                        ft.FilledButton(
                            content="Pagar con Webpay",
                            icon=ft.Icons.PAYMENTS,
                            height=48,
                            on_click=lambda e: controller.run_async(controller.handle_checkout()),
                            disabled=not controller.state.cart,
                            style=primary_button_style(),
                        ),
                        ft.OutlinedButton(
                            content="Verificar pago",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            on_click=lambda e: controller.run_async(controller.check_pending_payment()),
                            disabled=not controller.state.current_user,
                            style=outline_button_style(),
                        ),
                    ],
                ),
                padding=16,
            ),
        ],
    )


def build_cart_item(controller: "AppController", item: CartItem) -> ft.Control:
    def increase(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, 1)

    def decrease(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, -1)

    def remove(_: ft.ControlEvent) -> None:
        controller.handle_remove_from_cart(item.product.id)

    return card(
        ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                image_box(item.product.image, width=90, height=90, border_radius=14),
                ft.Column(
                    expand=True,
                    spacing=6,
                    controls=[
                        ft.Text(item.product.name, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                        ft.Text(currency(item.product.price), color=IschuuColors.TEXT_MUTED),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=IschuuColors.SKY, on_click=decrease),
                                ft.Text(str(item.quantity), size=16, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=IschuuColors.SUCCESS, on_click=increase),
                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=IschuuColors.DANGER, on_click=remove),
                            ],
                        ),
                    ],
                ),
                ft.Text(currency(item.product.price * item.quantity), weight=ft.FontWeight.BOLD, color=IschuuColors.VANILLA),
            ],
        ),
        padding=14,
    )
