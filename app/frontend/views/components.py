from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.views.theme import (
    IschuuColors,
    app_border,
    build_theme,
    pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_header(controller: "AppController") -> ft.Control:
    user = controller.state.current_user

    user_name = getattr(user, "name", "Invitado") if user else "Invitado"
    user_points = getattr(user, "points", 0) if user else 0

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=18, vertical=18),
        border_radius=24,
        gradient=ft.LinearGradient(
            colors=[
                "#111827",
                "#25172B",
                "#4C1D3F",
            ],
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            "Ischuu",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                            color=IschuuColors.CREAM,
                        ),
                        ft.Text(
                            f"Bienvenido, {user_name}",
                            size=13,
                            color=IschuuColors.TEXT_MUTED,
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                    border_radius=16,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    border=ft.Border(
                        left=ft.BorderSide(1, IschuuColors.PRIMARY),
                        top=ft.BorderSide(1, IschuuColors.PRIMARY),
                        right=ft.BorderSide(1, IschuuColors.PRIMARY),
                        bottom=ft.BorderSide(1, IschuuColors.PRIMARY),
                    ),
                    content=ft.Row(
                        spacing=8,
                        tight=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.STARS,
                                color=IschuuColors.VANILLA,
                                size=18,
                            ),
                            ft.Text(
                                str(user_points),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=IschuuColors.TEXT,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


def build_chip(label: str) -> ft.Control:
    return pill(label)


def build_summary_row(label: str, value: str, highlight: bool = False) -> ft.Control:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(
                label,
                color=IschuuColors.TEXT if highlight else IschuuColors.TEXT_MUTED,
                weight=ft.FontWeight.BOLD if highlight else ft.FontWeight.NORMAL,
            ),
            ft.Text(
                value,
                weight=ft.FontWeight.BOLD,
                size=16 if highlight else 14,
                color=IschuuColors.VANILLA if highlight else IschuuColors.TEXT,
            ),
        ],
    )


def build_navigation_bar(controller: "AppController") -> ft.NavigationBar:
    cart_count = getattr(controller.state, "cart_count", 0)

    cart_label = "Carrito"
    if cart_count > 0:
        cart_label = f"Carrito ({cart_count})"

    destinations = [
        ft.NavigationBarDestination(
            icon=ft.Icons.STOREFRONT_OUTLINED,
            selected_icon=ft.Icons.STOREFRONT,
            label="Tienda",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SHOPPING_CART_OUTLINED,
            selected_icon=ft.Icons.SHOPPING_CART,
            label=cart_label,
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.LOCAL_SHIPPING_OUTLINED,
            selected_icon=ft.Icons.LOCAL_SHIPPING,
            label="Pedidos",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.PERSON_OUTLINE,
            selected_icon=ft.Icons.PERSON,
            label="Perfil",
        ),
    ]

    if controller.is_admin():
        destinations.append(
            ft.NavigationBarDestination(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                selected_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                label="Admin",
            )
        )

    return ft.NavigationBar(
        selected_index=controller.current_section,
        bgcolor=IschuuColors.SURFACE,
        indicator_color=IschuuColors.PRIMARY_STRONG,
        destinations=destinations,
        on_change=controller.on_nav_change,
    )
