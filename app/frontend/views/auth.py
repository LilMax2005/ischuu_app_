from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.views.theme import (
    IschuuColors,
    card,
    input_style,
    muted_text,
    outline_button_style,
    primary_button_style,
    section_title,
    soft_card,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_auth_gate(controller: "AppController") -> ft.Control:
    auth_mode = getattr(controller, "auth_mode", "login")

    return ft.Column(
        spacing=16,
        controls=[
            _build_auth_header(),
            build_login_view(controller)
            if auth_mode == "login"
            else build_register_view(controller),
        ],
    )


def _build_auth_header() -> ft.Control:
    return ft.Container(
        padding=22,
        border_radius=26,
        gradient=ft.LinearGradient(colors=IschuuColors.HEADER_GRADIENT),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.AUTO_AWESOME,
                            color=IschuuColors.VANILLA,
                            size=28,
                        ),
                        ft.Text(
                            "Ischuu",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=IschuuColors.CREAM,
                        ),
                    ],
                ),
                ft.Text(
                    "Blind boxes, coleccionables kawaii, puntos y seguimiento de pedidos.",
                    size=14,
                    color=IschuuColors.TEXT_MUTED,
                ),
            ],
        ),
    )


def build_login_view(controller: "AppController") -> ft.Control:
    email = ft.TextField(
        label="Correo",
        value="",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        **input_style(),
    )

    password = ft.TextField(
        label="Contraseña",
        value="",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        **input_style(),
    )

    def do_login(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.handle_login(
                email.value or "",
                password.value or "",
            )
        )
    def go_register(_: ft.ControlEvent) -> None:
        controller.auth_mode = "register"
        controller.render()

    return card(
        ft.Column(
            spacing=14,
            controls=[
                section_title("Iniciar sesión", 22),
                muted_text("Accede para guardar carrito, ver pedidos y acumular puntos."),
                soft_card(
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.INFO_OUTLINE,
                                color=IschuuColors.SKY,
                                size=18,
                            ),
                        ],
                    )
                ),
                email,
                password,
                ft.FilledButton(
                    content="Entrar",
                    icon=ft.Icons.LOGIN,
                    height=48,
                    on_click=do_login,
                    style=primary_button_style(),
                ),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Text(
                            "¿No tienes cuenta?",
                            color=IschuuColors.TEXT_MUTED,
                            size=13,
                        ),
                        ft.TextButton(
                            content="Crear cuenta",
                            icon=ft.Icons.PERSON_ADD_ALT_1,
                            on_click=go_register,
                        ),
                    ],
                ),
            ],
        ),
        padding=20,
    )


def build_register_view(controller: "AppController") -> ft.Control:
    name = ft.TextField(
        label="Nombre",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        **input_style(),
    )

    email = ft.TextField(
        label="Correo",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        **input_style(),
    )

    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        **input_style(),
    )

    def do_register(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.handle_register(
                name.value or "",
                email.value or "",
                password.value or "",
            )
        )

    def go_login(_: ft.ControlEvent) -> None:
        controller.auth_mode = "login"
        controller.render()

    return card(
        ft.Column(
            spacing=14,
            controls=[
                section_title("Crear cuenta", 22),
                muted_text("Regístrate para activar puntos, preferencias y seguimiento de compras."),
                name,
                email,
                password,
                ft.FilledButton(
                    content="Crear cuenta",
                    icon=ft.Icons.PERSON_ADD_ALT_1,
                    height=48,
                    on_click=do_register,
                    style=primary_button_style(),
                ),
                ft.OutlinedButton(
                    content="Ya tengo cuenta",
                    icon=ft.Icons.LOGIN,
                    on_click=go_login,
                    style=outline_button_style(),
                ),
            ],
        ),
        padding=20,
    )
