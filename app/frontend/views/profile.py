from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.views.components import build_summary_row
from app.frontend.views.theme import (
    IschuuColors,
    card,
    muted_text,
    outline_button_style,
    primary_button_style,
    section_title,
    soft_card,
    status_pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


def build_profile_view(controller: "AppController") -> ft.Control:
    user = controller.state.current_user

    if user is None:
        return card(
            ft.Column(
                spacing=10,
                controls=[
                    section_title("Perfil", 22),
                    muted_text("Debes iniciar sesión para ver tu perfil."),
                ],
            )
        )

    user_name = getattr(user, "name", "")
    user_email = getattr(user, "email", "")
    user_points = int(getattr(user, "points", 0))
    favorite_categories = getattr(user, "favorite_categories", []) or []
    notifications_enabled = bool(getattr(user, "notifications_enabled", True))
    is_admin = bool(getattr(user, "is_admin", False))

    notifications_switch = ft.Switch(value=notifications_enabled)

    def save_profile(_: ft.ControlEvent) -> None:
        controller.handle_save_profile(notifications_switch.value)

    def logout(_: ft.ControlEvent) -> None:
        controller.handle_logout()

    level = "Ischuu Gold" if user_points >= 100 else "Ischuu Starter"

    preferences_text = (
        ", ".join(favorite_categories)
        if favorite_categories
        else "Sin preferencias"
    )

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Perfil y fidelización", 22),

            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    width=52,
                                    height=52,
                                    border_radius=999,
                                    bgcolor=IschuuColors.SURFACE_ALT,
                                    content=ft.Icon(
                                        ft.Icons.PERSON,
                                        color=IschuuColors.PRIMARY,
                                        size=30,
                                    ),
                                ),
                                ft.Column(
                                    expand=True,
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            user_name,
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=IschuuColors.TEXT,
                                        ),
                                        ft.Text(
                                            user_email,
                                            color=IschuuColors.TEXT_MUTED,
                                        ),
                                    ],
                                ),
                                status_pill(
                                    "Admin" if is_admin else level,
                                    "pink" if is_admin else "info",
                                ),
                            ],
                        ),

                        ft.Divider(color=IschuuColors.BORDER),

                        build_summary_row(
                            "Puntos acumulados",
                            str(user_points),
                            highlight=True,
                        ),
                        build_summary_row("Nivel", level),
                        build_summary_row("Preferencias", preferences_text),
                    ],
                ),
                padding=16,
            ),

            card(
                ft.Column(
                    spacing=12,
                    controls=[
                        section_title("Notificaciones", 18),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Avisos de ofertas, stock y ferias presenciales",
                                    color=IschuuColors.TEXT_MUTED,
                                ),
                                notifications_switch,
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.FilledButton(
                                    content="Guardar",
                                    icon=ft.Icons.SAVE,
                                    on_click=save_profile,
                                    style=primary_button_style(),
                                ),
                                ft.OutlinedButton(
                                    content="Cerrar sesión",
                                    icon=ft.Icons.LOGOUT,
                                    on_click=logout,
                                    style=outline_button_style(),
                                ),
                            ],
                        ),
                    ],
                ),
                padding=16,
            ),

            soft_card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Programa de puntos",
                            size=17,
                            weight=ft.FontWeight.BOLD,
                            color=IschuuColors.TEXT,
                        ),
                        muted_text(
                            "Por cada $500 en productos pagados acumulas 1 punto."
                        ),
                        muted_text(
                            "Cada punto equivale a $50 de descuento en futuras compras."
                        ),
                        muted_text(
                            "Tus categorías favoritas se calculan según tu historial de compra."
                        ),
                    ],
                ),
                padding=16,
            ),
        ],
    )