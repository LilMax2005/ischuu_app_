from __future__ import annotations

from typing import TYPE_CHECKING
import flet as ft

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


def build_header(controller: "AppController") -> ft.Control:
    user_name = controller.state.current_user.name if controller.state.current_user else "Invitado"
    user_points = controller.state.current_user.points if controller.state.current_user else 0

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=18, vertical=18),
        border_radius=20,
        gradient=ft.LinearGradient(colors=["#ff4fa3", "#8b5cf6"]),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("Ischuu", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"Bienvenido, {user_name}", size=13, color=ft.Colors.WHITE70),
                    ],
                ),
                ft.Container(
                    bgcolor="#ffffff22",
                    border_radius=14,
                    padding=10,
                    content=ft.Column(
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.STARS, color=ft.Colors.AMBER_300),
                            ft.Text(str(user_points), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                    ),
                ),
            ],
        ),
    )


def build_chip(label: str) -> ft.Control:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        bgcolor="#ffffff10",
        content=ft.Text(label, size=12),
    )


def build_summary_row(label: str, value: str, highlight: bool = False) -> ft.Control:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(label, color=ft.Colors.WHITE if highlight else ft.Colors.WHITE70),
            ft.Text(
                value,
                weight=ft.FontWeight.BOLD,
                size=15 if highlight else 14,
                color=ft.Colors.AMBER_300 if highlight else ft.Colors.WHITE,
            ),
        ],
    )


def build_navigation_bar(controller: "AppController") -> ft.NavigationBar:
    return ft.NavigationBar(
        selected_index=controller.current_section,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.STOREFRONT_OUTLINED, selected_icon=ft.Icons.STOREFRONT, label="Tienda"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label="Carrito"),
            ft.NavigationBarDestination(icon=ft.Icons.LOCAL_SHIPPING_OUTLINED, selected_icon=ft.Icons.LOCAL_SHIPPING, label="Pedidos"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="Perfil"),
        ],
        on_change=controller.on_nav_change,
    )
