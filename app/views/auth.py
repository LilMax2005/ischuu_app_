from typing import TYPE_CHECKING
import flet as ft

from app.views.components import build_chip

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


def build_auth_gate(controller: "AppController") -> ft.Control:
    info_card = ft.Container(
        padding=18,
        border_radius=18,
        bgcolor="#1b1b1b",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Aplicación Ischuu", size=22, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "MVP desarrollado en Python + Flet para catálogo, carrito, pedidos, recompensas y enlaces sociales.",
                    size=14,
                    color=ft.Colors.WHITE70,
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        build_chip("Catálogo"),
                        build_chip("Carrito"),
                        build_chip("Pedidos"),
                        build_chip("Recompensas"),
                        build_chip("Redes Sociales"),
                    ],
                ),
            ],
        ),
    )

    return ft.Tabs(
        selected_index=0,
        animation_duration=250,
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Iniciar sesión"),
                        ft.Tab(label="Registrarse"),
                        ft.Tab(label="Vista previa"),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        build_login_view(controller),
                        build_register_view(controller),
                        info_card,
                    ],
                ),
            ],
        ),
    )


def build_login_view(controller: "AppController") -> ft.Control:
    email = ft.TextField(label="Correo", prefix_icon=ft.Icons.EMAIL_OUTLINED, border_radius=14)
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_radius=14,
    )

    def do_login(_: ft.Event[ft.FilledButton]) -> None:
        controller.handle_login(email.value or "", password.value or "")

    return ft.Container(
        padding=18,
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Text("Ingresa a tu cuenta", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Demo: demo@ischuu.cl / 1234", color=ft.Colors.WHITE70),
                email,
                password,
                ft.FilledButton(
                    content="Entrar",
                    icon=ft.Icons.LOGIN,
                    height=48,
                    on_click=do_login,
                ),
            ],
        ),
    )


def build_register_view(controller: "AppController") -> ft.Control:
    name = ft.TextField(label="Nombre", prefix_icon=ft.Icons.PERSON_OUTLINE, border_radius=14)
    email = ft.TextField(label="Correo", prefix_icon=ft.Icons.EMAIL_OUTLINED, border_radius=14)
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_radius=14,
    )

    def do_register(_: ft.Event[ft.FilledButton]) -> None:
        controller.handle_register(name.value or "", email.value or "", password.value or "")

    return ft.Container(
        padding=18,
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Text("Crea tu cuenta", size=20, weight=ft.FontWeight.BOLD),
                name,
                email,
                password,
                ft.FilledButton(
                    content="Crear cuenta",
                    icon=ft.Icons.PERSON_ADD_ALT_1,
                    height=48,
                    on_click=do_register,
                ),
            ],
        ),
    )