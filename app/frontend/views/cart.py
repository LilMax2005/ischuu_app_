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
    status_pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController

def build_shipping_address_card(controller) -> ft.Control:
    if controller.shipping_address_saved and not controller.shipping_address_editing:
        return card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=4,
                                controls=[
                                    section_title("Dirección de despacho", 18),
                                    ft.Text(
                                        controller.shipping_address_text(),
                                        color=IschuuColors.TEXT_MUTED,
                                        size=13,
                                    ),
                                    ft.Text(
                                        f"Recibe: {controller.shipping_recipient.value or ''} · Tel: {controller.shipping_phone.value or ''}",
                                        color=IschuuColors.TEXT_MUTED,
                                        size=12,
                                    ),
                                ],
                            ),
                            status_pill("Guardada", "success"),
                        ],
                    ),
                    ft.OutlinedButton(
                        content="Modificar dirección",
                        icon=ft.Icons.EDIT_LOCATION_ALT_OUTLINED,
                        on_click=lambda e: controller.handle_edit_shipping_address(),
                        style=outline_button_style(),
                    ),
                ],
            ),
            padding=16,
        )

    buttons = [
        ft.FilledButton(
            content="Guardar dirección",
            icon=ft.Icons.SAVE,
            on_click=lambda e: controller.run_async(
                controller.handle_save_shipping_address()
            ),
            style=primary_button_style(),
        )
    ]

    if controller.shipping_address_saved:
        buttons.append(
            ft.OutlinedButton(
                content="Cancelar edición",
                icon=ft.Icons.CANCEL_OUTLINED,
                on_click=lambda e: controller.handle_cancel_edit_shipping_address(),
                style=outline_button_style(),
            )
        )

    return card(
        ft.Column(
            spacing=12,
            controls=[
                section_title("Dirección de despacho", 18),
                muted_text(
                    "Ingresa los datos donde quieres recibir tu pedido. Esta sección se minimizará después de guardar."
                ),
                controller.shipping_recipient,
                controller.shipping_phone,
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.Container(
                            width=300,
                            content=controller.shipping_region,
                        ),
                        ft.Container(
                            width=300,
                            content=controller.shipping_comuna,
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.Container(
                            width=420,
                            content=controller.shipping_street,
                        ),
                        ft.Container(
                            width=160,
                            content=controller.shipping_number,
                        ),
                    ],
                ),
                controller.shipping_details,
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=buttons,
                ),
            ],
        ),
        padding=16,
    )


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

    if not controller.cart_quote_box.controls:
        controller.cart_quote_box.controls = [
            build_summary_row(
                "Total estimado",
                currency(total_to_pay),
                highlight=True,
            ),
            muted_text(
                "El total final se actualizará al calcular descuentos.",
                12,
            ),
        ]

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
            *items_controls,

            build_shipping_address_card(controller),

            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        controller.use_points_switch,
                        controller.cart_quote_box,
                        ft.FilledButton(
                            content="Pagar con Webpay",
                            icon=ft.Icons.PAYMENTS,
                            on_click=lambda e: controller.run_async(
                                controller.handle_checkout()
                            ),
                            disabled=not controller.state.cart,
                            style=primary_button_style(),
                        ),
                    ],
                ),
                padding=16,
            )
        ],
    )


def build_cart_item(controller: "AppController", item: CartItem) -> ft.Control:
    """Tarjeta vertical para móvil con controles táctiles visibles."""

    def increase(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, 1)

    def decrease(_: ft.ControlEvent) -> None:
        controller.handle_change_quantity(item.product.id, -1)

    def remove(_: ft.ControlEvent) -> None:
        controller.handle_remove_from_cart(item.product.id)

    return card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        image_box(
                            item.product.image,
                            width=78,
                            height=78,
                            border_radius=14,
                        ),
                        ft.Column(
                            expand=True,
                            spacing=5,
                            controls=[
                                ft.Text(
                                    item.product.name,
                                    weight=ft.FontWeight.BOLD,
                                    color=IschuuColors.TEXT,
                                    max_lines=3,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    currency(item.product.price),
                                    color=IschuuColors.TEXT_MUTED,
                                ),
                            ],
                        ),
                        ft.Text(
                            currency(item.product.price * item.quantity),
                            weight=ft.FontWeight.BOLD,
                            color=IschuuColors.VANILLA,
                        ),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=2,
                            tight=True,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_color=IschuuColors.SKY,
                                    tooltip="Disminuir cantidad",
                                    on_click=decrease,
                                ),
                                ft.Container(
                                    width=34,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text(
                                        str(item.quantity),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=IschuuColors.TEXT,
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                    icon_color=IschuuColors.SUCCESS,
                                    tooltip="Aumentar cantidad",
                                    on_click=increase,
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=IschuuColors.DANGER,
                            tooltip="Eliminar del carrito",
                            on_click=remove,
                        ),
                    ],
                ),
            ],
        ),
        padding=14,
    )

