from __future__ import annotations

from typing import Callable, Dict
import flet as ft

from app.models.state import AppState
from app.views.auth import build_auth_gate
from app.views.cart import build_cart_view
from app.views.components import build_header, build_navigation_bar
from app.views.orders import build_orders_view
from app.views.profile import build_profile_view
from app.views.store import build_store_view


class AppController:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.current_section = 0
        self.body = ft.Column(spacing=16, expand=True)

        self._configure_page()
        self._build_shared_controls()

        self.page.add(self.body)
        self.render()

    def _configure_page(self) -> None:
        self.page.title = "Ischuu App MVC"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.window_width = 420
        self.page.window_height = 900
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.bgcolor = "#121212"
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#ff4fa3",
                secondary="#8b5cf6",
                surface="#1e1e1e",
                error="#ef4444",
            )
        )

    def _build_shared_controls(self) -> None:
        self.search_field = ft.TextField(
            hint_text="Buscar blind box, anime o serie...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=14,
            filled=True,
            on_change=self.on_search,
        )
        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            value="Todas",
            border_radius=14,
            options=[ft.DropdownOption(key=category, text=category) for category in self.state.categories],
            on_select=self.on_category_change,
        )

    def render(self) -> None:
        self.category_dropdown.options = [ft.DropdownOption(key=category, text=category) for category in self.state.categories]
        self.category_dropdown.value = self.state.category_filter

        self.body.controls.clear()
        self.body.controls.append(build_header(self))

        if not self.state.current_user:
            self.body.controls.append(build_auth_gate(self))
        else:
            self.body.controls.append(ft.Container(content=self.build_section(), expand=True))
            self.body.controls.append(build_navigation_bar(self))

        self.page.update()

    def build_section(self) -> ft.Control:
        sections: Dict[int, Callable[[], ft.Control]] = {
            0: lambda: build_store_view(self),
            1: lambda: build_cart_view(self),
            2: lambda: build_orders_view(self.state.orders),
            3: lambda: build_profile_view(self),
        }
        return sections[self.current_section]()

    def handle_login(self, email: str, password: str) -> None:
        if self.state.login(email, password):
            self.show_message("Sesión iniciada correctamente.")
            self.render()
            return
        self.show_message("Credenciales inválidas.", error=True)

    def handle_register(self, name: str, email: str, password: str) -> None:
        if not name.strip() or not email.strip() or not password.strip():
            self.show_message("Completa todos los campos.", error=True)
            return

        ok, message = self.state.register(name, email, password)
        self.show_message(message, error=not ok)
        if ok:
            self.state.login(email, password)
            self.render()

    def handle_add_to_cart(self, product_id: str) -> None:
        try:
            self.state.add_to_cart(product_id)
            product = next(product for product in self.state.products if product.id == product_id)
            self.show_message(f"{product.name} agregado al carrito.")
            self.render()
        except ValueError as exc:
            self.show_message(str(exc), error=True)

    def handle_change_quantity(self, product_id: str, delta: int) -> None:
        try:
            self.state.change_quantity(product_id, delta)
            self.render()
        except ValueError as exc:
            self.show_message(str(exc), error=True)

    def handle_checkout(self, _: ft.Event[ft.Button]) -> None:
        try:
            order = self.state.place_order()
            self.current_section = 2
            self.show_message(f"Pedido {order.id} generado correctamente.")
            self.render()
        except (ValueError, PermissionError) as exc:
            self.show_message(str(exc), error=True)

    def handle_save_profile(self, notifications_enabled: bool) -> None:
        if self.state.current_user:
            self.state.current_user.notifications_enabled = notifications_enabled
        self.show_message("Preferencias guardadas correctamente.")

    def handle_logout(self) -> None:
        self.state.logout()
        self.current_section = 0
        self.search_field.value = ""
        self.show_message("Sesión cerrada.")
        self.render()

    def on_search(self, event: ft.Event[ft.TextField]) -> None:
        self.state.search_text = event.control.value or ""
        self.render()

    def on_category_change(self, event: ft.Event[ft.Dropdown]) -> None:
        self.state.category_filter = event.control.value or "Todas"
        self.render()

    def on_nav_change(self, event: ft.Event[ft.NavigationBar]) -> None:
        self.current_section = event.control.selected_index or 0
        self.render()

    def show_message(self, message: str, error: bool = False) -> None:
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
            open=True,
        )
        self.page.update()
