from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.views.theme import (
    IschuuColors,
    app_border,
    pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_header(controller: "AppController") -> ft.Control:
    """Encabezado compacto y seguro para pantallas móviles."""
    user = controller.state.current_user
    user_name = getattr(user, "name", "Invitado") if user else "Invitado"
    user_points = max(0, int(getattr(user, "points", 0))) if user else 0

    # En móvil se evita una fila muy ancha: el nombre ocupa el espacio
    # disponible y los puntos se muestran siempre en una segunda fila.
    return ft.Container(
        padding=ft.Padding(left=16, top=16, right=16, bottom=14),
        border_radius=24,
        gradient=ft.LinearGradient(colors=IschuuColors.HEADER_GRADIENT),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    "Ischuu",
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=IschuuColors.CREAM,
                                ),
                                ft.Text(
                                    f"Bienvenido, {user_name}",
                                    size=12,
                                    color=IschuuColors.TEXT_MUTED,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=(
                                ft.Icons.LIGHT_MODE_OUTLINED
                                if controller.is_light_theme
                                else ft.Icons.DARK_MODE_OUTLINED
                            ),
                            icon_color=IschuuColors.PRIMARY,
                            tooltip=(
                                "Cambiar a tema oscuro"
                                if controller.is_light_theme
                                else "Cambiar a tema claro"
                            ),
                            on_click=lambda _e: controller.toggle_theme(),
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                    border_radius=16,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    border=app_border(IschuuColors.PRIMARY),
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
                                f"Puntos acumulados: {user_points}",
                                size=13,
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
        ft.NavigationBarDestination(
            icon=ft.Icons.HELP_OUTLINE,
            selected_icon=ft.Icons.HELP,
            label="Ayuda",
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

    max_index = len(destinations) - 1
    selected_index = int(getattr(controller, "current_section", 0))

    if selected_index < 0 or selected_index > max_index:
        selected_index = 0
        controller.current_section = 0

    return ft.NavigationBar(
        selected_index=selected_index,
        bgcolor=IschuuColors.SURFACE,
        indicator_color=IschuuColors.PRIMARY_STRONG,
        destinations=destinations,
        on_change=controller.on_nav_change,
    )
