from __future__ import annotations

from typing import TYPE_CHECKING
import flet as ft

from app.views.components import build_summary_row

if TYPE_CHECKING:
    from app.controllers.app_controller import AppController


def build_profile_view(controller: "AppController") -> ft.Control:
    user = controller.state.current_user
    assert user is not None

    notifications_switch = ft.Switch(value=user.notifications_enabled)

    def save_profile(_: ft.ControlEvent) -> None:
        controller.handle_save_profile(notifications_switch.value)

    def logout(_: ft.ControlEvent) -> None:
        controller.handle_logout()

    return ft.Column(
        spacing=14,
        controls=[
            ft.Text("Perfil y fidelización", size=22, weight=ft.FontWeight.BOLD),
            ft.Container(
                padding=16,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(user.name, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(user.email, color=ft.Colors.WHITE70),
                        ft.Divider(color="#ffffff12"),
                        build_summary_row("Puntos acumulados", str(user.points), highlight=True),
                        build_summary_row("Nivel", "Otaku Gold" if user.points >= 100 else "Otaku Starter"),
                        build_summary_row(
                            "Preferencias",
                            ", ".join(user.favorite_categories) if user.favorite_categories else "Sin preferencias",
                        ),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Notificaciones", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Recibir avisos de ofertas, stock y ferias presenciales"),
                                notifications_switch,
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.FilledButton(content="Guardar", icon=ft.Icons.SAVE, on_click=save_profile),
                                ft.OutlinedButton(content="Cerrar sesión", icon=ft.Icons.LOGOUT, on_click=logout),
                            ],
                        ),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=18,
                bgcolor="#1b1b1b",
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Integraciones futuras", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• FastAPI para productos, usuarios, pedidos y pagos", color=ft.Colors.WHITE70),
                        ft.Text("• JWT para autenticación segura", color=ft.Colors.WHITE70),
                        ft.Text("• PostgreSQL o MongoDB en la nube", color=ft.Colors.WHITE70),
                        ft.Text("• Push notifications y analítica de uso", color=ft.Colors.WHITE70),
                    ],
                ),
            ),
        ],
    )
