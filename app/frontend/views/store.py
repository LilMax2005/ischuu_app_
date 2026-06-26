from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.models.entities import Product
from app.frontend.utils.formatters import currency
from app.frontend.views.theme import (
    IschuuColors,
    card,
    image_box,
    muted_text,
    outline_button_style,
    pill,
    primary_button_style,
    section_title,
    soft_card,
    status_pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_store_view(controller: "AppController") -> ft.Control:
    controller.refresh_product_list()

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Catálogo Ischuu", 22),
            muted_text("Explora blind box de anime, kawaii y coleccionables seleccionados."),
            controller.search_field,
            controller.category_dropdown,
            controller.product_list,
            build_catalog_pagination(controller),
            build_social_banner(controller),
        ],
    )


def build_product_card(controller: "AppController", product: Product) -> ft.Control:
    badge_status = "success" if product.is_original else "warning"
    badge_label = "Original" if product.is_original else "Alternativo"
    has_stock = int(product.stock) > 0

    def add(_: ft.ControlEvent) -> None:
        controller.handle_add_to_cart(product.id)

    return card(
        ft.Column(
            spacing=12,
            controls=[
                image_box(product.image, height=180, border_radius=18),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                    controls=[
                        pill(product.category, ft.Icons.CATEGORY_OUTLINED),
                        pill(product.rarity, ft.Icons.AUTO_AWESOME),
                    ],
                ),
                ft.Text(product.name, size=18, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                ft.Text(product.series, color=IschuuColors.TEXT_MUTED),
                ft.Text(product.description, size=13, color=IschuuColors.TEXT_SOFT),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(currency(product.price), size=20, weight=ft.FontWeight.BOLD, color=IschuuColors.VANILLA),
                                (
                                    ft.Text(f"Stock: {product.stock}", size=12, color=IschuuColors.TEXT_MUTED)
                                    if has_stock
                                    else status_pill("SIN STOCK", "danger")
                                ),
                            ],
                        ),
                        status_pill(badge_label, badge_status),
                    ],
                ),
                ft.FilledButton(
                    content="Agregar al carrito",
                    icon=ft.Icons.ADD_SHOPPING_CART,
                    on_click=add,
                    disabled=not has_stock,
                    style=primary_button_style(),
                ),
            ],
        ),
        padding=14,
    )


def build_catalog_pagination(controller: "AppController") -> ft.Control:
    current_page = int(getattr(controller.state, "product_page", 1) or 1)
    total_pages = max(1, int(getattr(controller.state, "product_total_pages", 1) or 1))
    total = int(getattr(controller.state, "product_total", 0) or 0)
    start = max(1, current_page - 2)
    end = min(total_pages, start + 4)
    start = max(1, end - 4)
    page_numbers = list(range(start, end + 1))

    controls: list[ft.Control] = [
        ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Página anterior",
            disabled=current_page <= 1,
            on_click=lambda _e: controller.set_catalog_page(current_page - 1),
        )
    ]
    controls.extend(
        [
            ft.FilledButton(
                content=str(page),
                on_click=lambda _e, page=page: controller.set_catalog_page(page),
                style=primary_button_style() if page == current_page else outline_button_style(),
            )
            for page in page_numbers
        ]
    )
    controls.append(
        ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="Página siguiente",
            disabled=current_page >= total_pages,
            on_click=lambda _e: controller.set_catalog_page(current_page + 1),
        )
    )

    return soft_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        controller.catalog_page_size_dropdown,
                        ft.Text(
                            f"Página {current_page} de {total_pages} · {total} productos",
                            color=IschuuColors.TEXT_MUTED,
                            size=12,
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=6,
                    run_spacing=6,
                    controls=controls,
                ),
            ],
        ),
        padding=12,
    )


def build_social_banner(controller: "AppController") -> ft.Control:
    async def open_instagram(e) -> None:
        await controller.page.launch_url("https://www.instagram.com/ischuu._")

    async def open_tiktok(e) -> None:
        await controller.page.launch_url("https://www.tiktok.com/ischuu._")

    return soft_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, color=IschuuColors.PRIMARY),
                        ft.Text("Síguenos en redes", size=18, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                    ],
                ),
                muted_text("Mira novedades, reels, clientes felices y próximos lanzamientos."),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        ft.OutlinedButton(
                            content="Instagram",
                            icon=ft.Icons.CAMERA_ALT_OUTLINED,
                            on_click=open_instagram,
                            style=outline_button_style(),
                        ),
                        ft.OutlinedButton(
                            content="TikTok",
                            icon=ft.Icons.MUSIC_NOTE_OUTLINED,
                            on_click=open_tiktok,
                            style=outline_button_style(),
                        ),
                    ],
                ),
            ],
        ),
        padding=16,
    )
