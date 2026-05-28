from __future__ import annotations

from typing import TYPE_CHECKING, List
import flet as ft

from app.models.entities import Product
from app.utils.formatters import currency

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


def build_store_view(controller: "AppController") -> ft.Control:
    product_cards: List[ft.Control] = [build_product_card(controller, product) for product in controller.state.filtered_products]

    if not product_cards:
        product_cards = [
            ft.Container(
                padding=20,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Text("No se encontraron productos con ese filtro."),
            )
        ]

    return ft.Column(
        spacing=14,
        controls=[
            ft.Text("Tienda", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Explora blind box de anime, videojuegos y coleccionables.", color=ft.Colors.WHITE70),
            controller.search_field,
            controller.category_dropdown,
            build_social_banner(controller),
            ft.Column(spacing=12, controls=product_cards),
        ],
    )


def build_product_card(controller: "AppController", product: Product) -> ft.Control:
    badge_color = ft.Colors.GREEN_400 if product.is_original else ft.Colors.ORANGE_300

    def add(_: ft.ControlEvent) -> None:
        controller.handle_add_to_cart(product.id)

    return ft.Container(
        padding=14,
        border_radius=18,
        bgcolor="#1b1b1b",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Image(src=product.image, height=170, fit=ft.BoxFit.COVER, border_radius=14),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            bgcolor="#ffffff14",
                            border_radius=999,
                            content=ft.Text(product.category, size=12),
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            bgcolor="#ffffff14",
                            border_radius=999,
                            content=ft.Text(product.rarity, size=12),
                        ),
                    ],
                ),
                ft.Text(product.name, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(product.series, color=ft.Colors.WHITE70),
                ft.Text(product.description, size=13, color=ft.Colors.WHITE60),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(currency(product.price), size=19, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Stock: {product.stock}", size=12, color=ft.Colors.WHITE70),
                            ],
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            border_radius=999,
                            bgcolor="#ffffff14",
                            content=ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.VERIFIED, color=badge_color, size=18),
                                    ft.Text("Original" if product.is_original else "Alternativo", size=12),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.FilledButton(
                    content="Agregar al carrito",
                    icon=ft.Icons.ADD_SHOPPING_CART,
                    on_click=add,
                    disabled=product.stock <= 0,
                ),
            ],
        ),
    )


def build_social_banner(controller: "AppController") -> ft.Control:
    def open_instagram(_: ft.ControlEvent) -> None:
        controller.page.launch_url("https://www.instagram.com/ischuu._")

    def open_tiktok(_: ft.ControlEvent) -> None:
        controller.page.launch_url("https://www.tiktok.com/")

    return ft.Container(
        padding=16,
        border_radius=18,
        bgcolor="#1b1b1b",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Integración social", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Desde aquí puedes dirigir a los clientes a Instagram y TikTok para reforzar campañas, reels y contenido promocional.",
                    size=13,
                    color=ft.Colors.WHITE70,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(content="Instagram", icon=ft.Icons.CAMERA_ALT_OUTLINED, on_click=open_instagram),
                        ft.OutlinedButton(content="TikTok", icon=ft.Icons.MUSIC_NOTE_OUTLINED, on_click=open_tiktok),
                    ]
                ),
            ],
        ),
    )
