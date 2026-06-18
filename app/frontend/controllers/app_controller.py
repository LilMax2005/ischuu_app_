from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import flet as ft
import httpx

from app.frontend.models.entities import CartItem, Product, User
from app.frontend.models.state import AppState
from app.frontend.services.api_client import ApiClient
from app.frontend.utils.formatters import currency
from app.frontend.views.admin import build_admin_view
from app.frontend.views.auth import build_auth_gate
from app.frontend.views.cart import build_cart_view
from app.frontend.views.components import build_header, build_navigation_bar
from app.frontend.views.help import build_help_view
from app.frontend.views.orders import build_orders_view
from app.frontend.views.profile import build_profile_view
from app.frontend.views.store import build_product_card, build_store_view
from app.frontend.views.theme import (
    IschuuColors,
    apply_palette,
    build_theme,
    input_style,
)

CART_FILE = Path("ischuu_cart_local.json")
PENDING_PAYMENT_FILE = Path("ischuu_pending_payment.json")
SHIPPING_ADDRESS_FILE = Path("ischuu_shipping_address.json")


class AppController:
    def __init__(self, page: ft.Page, api_base_url: str) -> None:
        self.page = page
        self.api = ApiClient(api_base_url)
        self.state = AppState()
        self.is_light_theme = True
        apply_palette(self.is_light_theme)
        self.onesignal = None
        self.push_service_ready = False
        self.push_permission_granted = False
        self.pending_push_route: str | None = None

        # Dirección de despacho
        self.shipping_address_saved = False
        self.shipping_address_editing = True

        self.current_section = 0
        self.auth_mode = "login"
        self.cart_quote: dict[str, Any] = {}
        self.payment_polling = False

        self.shipping_recipient = ft.TextField(
            label="Nombre destinatario",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            **input_style(),
        )

        self.shipping_phone = ft.TextField(
            label="Teléfono",
            prefix_icon=ft.Icons.PHONE_OUTLINED,
            **input_style(),
        )

        self.shipping_region = ft.TextField(
            label="Región",
            value="Región Metropolitana",
            prefix_icon=ft.Icons.MAP_OUTLINED,
            **input_style(),
        )

        self.shipping_comuna = ft.TextField(
            label="Comuna",
            prefix_icon=ft.Icons.LOCATION_CITY_OUTLINED,
            **input_style(),
        )

        self.shipping_street = ft.TextField(
            label="Calle",
            prefix_icon=ft.Icons.HOME_OUTLINED,
            **input_style(),
        )

        self.shipping_number = ft.TextField(
            label="Número",
            prefix_icon=ft.Icons.TAG_OUTLINED,
            **input_style(),
        )

        self.shipping_details = ft.TextField(
            label="Referencia / Depto / Casa / Indicaciones",
            prefix_icon=ft.Icons.NOTES_OUTLINED,
            **input_style(),
        )

        self.admin_tab = "dashboard"
        self.admin_summary: dict[str, Any] = {}
        self.admin_users: list[dict] = []
        self.admin_products: list[dict] = []
        self.admin_orders: list[dict] = []
        self.admin_settings: dict[str, Any] = {}

        self.page.title = "Ischuu"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 18
        self.page.bgcolor = IschuuColors.BG
        self.page.theme = build_theme()
        self.page.scroll = ft.ScrollMode.AUTO

        self.body = ft.Column(spacing=16, expand=True)
        self.product_list = ft.Column(spacing=12)
        self.cart_quote_box = ft.Column(spacing=6)

        self.search_field = ft.TextField(
            hint_text="Buscar producto, serie o categoría...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search,
            **input_style(),
        )

        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            value="Todas",
            options=[ft.dropdown.Option("Todas")],
            on_select=self.on_category_change,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
        )

        self.use_points_switch = ft.Switch(
            label="Usar puntos disponibles",
            value=False,
            on_change=lambda e: self.run_async(self.refresh_cart_quote()),
        )

        self.navbar = build_navigation_bar(self)
        self.page.navigation_bar = self.navbar
        self.page.add(self.body)

        self.help_category = "inicio"
        self.help_search_query = ""
        self.help_open_question: int | None = None

        self.render()
        self.run_async(self.startup_load())

    def run_async(self, coro) -> None:
        try:
            asyncio.get_event_loop().create_task(coro)
        except RuntimeError:
            asyncio.run(coro)

    def _apply_theme_to_persistent_controls(self) -> None:
        text_field_style = input_style()
        text_fields = [
            self.shipping_recipient,
            self.shipping_phone,
            self.shipping_region,
            self.shipping_comuna,
            self.shipping_street,
            self.shipping_number,
            self.shipping_details,
            self.search_field,
        ]

        for text_field in text_fields:
            for property_name, value in text_field_style.items():
                setattr(text_field, property_name, value)

        self.category_dropdown.bgcolor = IschuuColors.SURFACE_ALT
        self.category_dropdown.color = IschuuColors.TEXT
        self.category_dropdown.border_color = IschuuColors.BORDER
        self.category_dropdown.focused_border_color = IschuuColors.PRIMARY_STRONG
        self.category_dropdown.label_style = ft.TextStyle(color=IschuuColors.TEXT_MUTED)

    def toggle_theme(self) -> None:
        self.is_light_theme = not self.is_light_theme
        apply_palette(self.is_light_theme)

        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if self.is_light_theme else ft.ThemeMode.DARK
        )
        self.page.bgcolor = IschuuColors.BG
        self.page.theme = build_theme()
        self._apply_theme_to_persistent_controls()
        self.render()

    def _is_mobile_platform(self) -> bool:
        platform = str(getattr(self.page, "platform", "") or "").lower()
        return "android" in platform or "ios" in platform

    def on_push_notification_click(self, _event) -> None:
        self.pending_push_route = "orders"

        if self.state.current_user is None:
            return

        self.current_section = 2
        self.pending_push_route = None
        self.run_async(self.load_orders())
        self.render()

    def on_push_notification_foreground(self, _event) -> None:
        if self.state.current_user is not None:
            self.run_async(self.load_orders())

    async def setup_push_notifications(self) -> bool:
        if self.onesignal is not None:
            return True

        if not self._is_mobile_platform():
            return False

        try:
            config = await self.api.get_notification_config()
            app_id = str(config.get("app_id", "")).strip()
            if not config.get("enabled") or not app_id:
                return False

            import flet_onesignal as fos

            self.onesignal = fos.OneSignal(
                app_id=app_id,
                on_notification_click=self.on_push_notification_click,
                on_notification_foreground=self.on_push_notification_foreground,
            )
            self.page.services.append(self.onesignal)
            self.push_service_ready = True
            self.page.update()
            return True
        except Exception as exc:
            print(f"Notificaciones móviles no disponibles: {exc}")
            self.onesignal = None
            self.push_service_ready = False
            return False

    async def activate_push_for_current_user(self) -> None:
        user = self.state.current_user
        if user is None:
            return

        if self.onesignal is None and not await self.setup_push_notifications():
            return

        try:
            await self.onesignal.login(str(user.id))
            await self.onesignal.user.set_language("es")

            if bool(user.notifications_enabled):
                granted = await self.onesignal.notifications.request_permission(
                    fallback_to_settings=True
                )
                self.push_permission_granted = bool(granted)
                if granted:
                    await self.onesignal.user.opt_in_push()
            else:
                await self.onesignal.user.opt_out_push()
                self.push_permission_granted = False
        except Exception as exc:
            print(f"No se pudo vincular el teléfono a las notificaciones: {exc}")

    async def disconnect_push_user(self) -> None:
        if self.onesignal is None:
            return

        try:
            await self.onesignal.logout()
        except Exception as exc:
            print(f"No se pudo cerrar la sesión de notificaciones: {exc}")

    def handle_save_profile(self, notifications_enabled: bool) -> None:
        self.run_async(
            self.save_notification_preference(bool(notifications_enabled))
        )

    async def save_notification_preference(self, enabled: bool) -> None:
        try:
            effective_enabled = enabled

            if enabled and self.onesignal is None:
                await self.setup_push_notifications()

            if self.onesignal is not None:
                if enabled:
                    granted = await self.onesignal.notifications.request_permission(
                        fallback_to_settings=True
                    )
                    self.push_permission_granted = bool(granted)
                    effective_enabled = bool(granted)
                    if granted:
                        await self.onesignal.login(str(self.state.current_user.id))
                        await self.onesignal.user.opt_in_push()
                else:
                    await self.onesignal.user.opt_out_push()
                    self.push_permission_granted = False

            user_data = await self.api.update_notification_preference(
                effective_enabled
            )
            self.state.current_user = self.user_from_dict(user_data)

            if enabled and not effective_enabled:
                self.show_message(
                    "Debes autorizar las notificaciones en los ajustes del teléfono.",
                    error=True,
                )
            else:
                message = (
                    "Notificaciones de pedidos activadas."
                    if effective_enabled
                    else "Notificaciones de pedidos desactivadas."
                )
                self.show_message(message)

            self.render()
        except Exception as exc:
            self.show_message(
                f"No se pudo guardar la preferencia de notificaciones: {exc}",
                error=True,
            )

    def apply_shipping_address_to_fields(self, data: dict | None) -> None:
        data = data or {}

        self.shipping_recipient.value = data.get("recipient", "")
        self.shipping_phone.value = data.get("phone", "")
        self.shipping_region.value = data.get("region", "Región Metropolitana")
        self.shipping_comuna.value = data.get("comuna", "")
        self.shipping_street.value = data.get("street", "")
        self.shipping_number.value = data.get("number", "")
        self.shipping_details.value = data.get("details", "")

        self.shipping_address_saved = self.shipping_address_is_complete()
        self.shipping_address_editing = not self.shipping_address_saved

    def select_help_category(self, category: str) -> None:
        self.help_category = category or "inicio"
        self.help_search_query = ""
        self.help_open_question = None
        self.render()

    def toggle_help_question(self, question_index: int) -> None:
        if self.help_open_question == question_index:
            self.help_open_question = None
        else:
            self.help_open_question = question_index

        self.render()

    def on_help_search(self, e) -> None:
        self.set_help_search(e.control.value)

    def set_help_search(self, query: str | None) -> None:
        self.help_search_query = str(query or "").strip()
        if self.help_search_query:
            self.help_category = "preguntas"
        self.help_open_question = None
        self.render()

    def clear_help_search(self) -> None:
        self.help_search_query = ""
        self.help_open_question = None
        self.render()

    def open_orders_from_help(self) -> None:
        if not self.state.current_user:
            self.show_message(
                "Debes iniciar sesión para revisar tus pedidos.",
                error=True,
            )
            return

        self.current_section = 2
        self.run_async(self.load_orders())
        self.render()

    def open_help_whatsapp(self) -> None:
        phone = "56961934594"
        message = "Hola, necesito ayuda con la aplicación Ischuu."
        url = f"https://wa.me/{phone}?text={quote(message)}"

        self.page.launch_url(url)

    def open_help_email(self) -> None:
        email = "soporte@ischuu.cl"
        subject = "Solicitud de ayuda - Ischuu"

        self.page.launch_url(f"mailto:{email}?subject={quote(subject)}")

    def shipping_address_payload(self) -> dict:
        return {
            "recipient": self.shipping_recipient.value or "",
            "phone": self.shipping_phone.value or "",
            "region": self.shipping_region.value or "",
            "comuna": self.shipping_comuna.value or "",
            "street": self.shipping_street.value or "",
            "number": self.shipping_number.value or "",
            "details": self.shipping_details.value or "",
        }

    def shipping_address_is_complete(self) -> bool:
        data = self.shipping_address_payload()

        required = [
            "recipient",
            "phone",
            "region",
            "comuna",
            "street",
            "number",
        ]

        return all(str(data.get(field, "")).strip() for field in required)

    def shipping_address_text(self) -> str:
        data = self.shipping_address_payload()

        address = (
            f"{data.get('street', '').strip()} "
            f"{data.get('number', '').strip()}, "
            f"{data.get('comuna', '').strip()}, "
            f"{data.get('region', '').strip()}"
        )

        details = data.get("details", "").strip()

        if details:
            address = f"{address}. Ref: {details}"

        return address

    def show_message(self, message: str, error: bool = False) -> None:
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=IschuuColors.ON_PRIMARY),
            bgcolor=IschuuColors.DANGER if error else IschuuColors.SUCCESS,
            open=True,
        )
        self.page.update()

    def user_from_dict(self, user_data: dict) -> User:
        return User(
            id=user_data.get("id", ""),
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            points=int(user_data.get("points", 0)),
            favorite_categories=user_data.get("favorite_categories", []),
            notifications_enabled=bool(user_data.get("notifications_enabled", True)),
            is_admin=bool(user_data.get("is_admin", False)),
            is_active=bool(user_data.get("is_active", True)),
            shipping_address=user_data.get("shipping_address", {}) or {},
        )

    def is_admin(self) -> bool:
        user = self.state.current_user

        if not user:
            return False

        return bool(getattr(user, "is_admin", False))

    def render(self) -> None:
        if self.current_section == 5 and not self.is_admin():
            self.current_section = 0

        self.body.controls.clear()
        self.body.controls.append(build_header(self))
        self.body.controls.append(self.build_section())

        self.navbar = build_navigation_bar(self)
        self.navbar.selected_index = self.current_section
        self.page.navigation_bar = self.navbar

        self.page.update()

    def save_shipping_address_to_file(self) -> None:
        data = self.shipping_address_payload()

        SHIPPING_ADDRESS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_shipping_address_from_file(self) -> None:
        if not SHIPPING_ADDRESS_FILE.exists():
            self.shipping_address_saved = False
            self.shipping_address_editing = True
            return

        try:
            data = json.loads(
                SHIPPING_ADDRESS_FILE.read_text(encoding="utf-8")
            )

            self.shipping_recipient.value = data.get("recipient", "")
            self.shipping_phone.value = data.get("phone", "")
            self.shipping_region.value = data.get("region", "Región Metropolitana")
            self.shipping_comuna.value = data.get("comuna", "")
            self.shipping_street.value = data.get("street", "")
            self.shipping_number.value = data.get("number", "")
            self.shipping_details.value = data.get("details", "")

            self.shipping_address_saved = self.shipping_address_is_complete()
            self.shipping_address_editing = not self.shipping_address_saved

        except Exception:
            self.shipping_address_saved = False
            self.shipping_address_editing = True

    async def handle_save_shipping_address(self) -> None:
        if not self.state.current_user:
            self.show_message(
                "Debes iniciar sesión para guardar la dirección.",
                error=True,
            )
            return

        if not self.shipping_address_is_complete():
            self.show_message(
                "Completa los datos obligatorios de despacho.",
                error=True,
            )
            return

        try:
            updated_user = await self.api.update_my_shipping_address(
                self.shipping_address_payload()
            )

            self.apply_shipping_address_to_fields(
                getattr(self.state.current_user, "shipping_address", {}) or {}
            )

            self.shipping_address_saved = True
            self.shipping_address_editing = False

            self.show_message("Dirección de despacho guardada correctamente.")
            self.render()

        except Exception as exc:
            self.show_message(
                f"No se pudo guardar la dirección: {exc}",
                error=True,
            )

    def handle_edit_shipping_address(self) -> None:
        self.shipping_address_editing = True
        self.render()

    def handle_cancel_edit_shipping_address(self) -> None:
        if self.shipping_address_saved:
            self.shipping_address_editing = False
            self.render()

    def build_section(self) -> ft.Control:
        if self.current_section == 0:
            return build_store_view(self)

        if self.current_section == 1:
            return build_cart_view(self)

        if self.current_section == 2:
            return build_orders_view(self)

        if self.current_section == 3:
            if not self.state.current_user:
                return build_auth_gate(self)

            return build_profile_view(self)

        if self.current_section == 4:
            return build_help_view(self)

        if self.current_section == 5 and self.is_admin():
            return build_admin_view(self)

        self.current_section = 0
        return build_store_view(self)

    async def startup_load(self) -> None:
        await self.setup_push_notifications()

        try:
            await self.load_products()
            self.load_cart_from_file()
            self.load_shipping_address_from_file()
            self.refresh_product_list()
            self.render()
        except Exception as exc:
            self.show_message(f"No se pudo cargar catálogo: {exc}", error=True)

    async def load_products(self) -> None:
        data = await self.api.get_products()
        self.state.products = [
            Product(
                id=p["id"],
                name=p["name"],
                series=p.get("series", ""),
                price=int(p.get("price", 0)),
                stock=int(p.get("stock", 0)),
                category=p.get("category", "General"),
                rarity=p.get("rarity", "Común"),
                description=p.get("description", ""),
                is_original=bool(p.get("is_original", True)),
                image=p.get("image_url", ""),
            )
            for p in data
        ]

        self.category_dropdown.options = [
            ft.dropdown.Option(category)
            for category in self.state.categories
        ]

    async def load_orders(self) -> None:
        if not self.state.current_user:
            self.state.orders = []
            return

        try:
            self.state.orders = await self.api.get_orders()
        except Exception:
            self.state.orders = []

    async def refresh_me(self) -> None:
        if not self.state.current_user:
            return

        try:
            user_data = await self.api.get_me()
            self.state.current_user = self.user_from_dict(user_data)

            await self.activate_push_for_current_user()

            if self.pending_push_route == "orders":
                self.current_section = 2
                self.pending_push_route = None
        except Exception:
            pass

    async def refresh_me_and_render(self) -> None:
        await self.refresh_me()
        self.render()

    def refresh_product_list(self) -> None:
        cards = [
            build_product_card(self, product)
            for product in self.state.filtered_products
        ]

        if not cards:
            from app.frontend.views.theme import card, muted_text

            cards = [
                card(
                    muted_text("No se encontraron productos con ese filtro."),
                    padding=20,
                )
            ]

        self.product_list.controls = cards

    def save_cart_to_file(self) -> None:
        data = [
            {"product_id": item.product.id, "quantity": item.quantity}
            for item in self.state.cart
        ]

        CART_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_cart_from_file(self) -> None:
        if not CART_FILE.exists():
            return

        try:
            data = json.loads(CART_FILE.read_text(encoding="utf-8"))
            self.state.cart.clear()

            for row in data:
                product = next(
                    (p for p in self.state.products if p.id == row.get("product_id")),
                    None,
                )

                if product:
                    self.state.cart.append(
                        CartItem(
                            product=product,
                            quantity=max(1, int(row.get("quantity", 1))),
                        )
                    )

        except Exception:
            self.state.cart = []

    def clear_cart_file(self) -> None:
        self.state.cart.clear()

        if CART_FILE.exists():
            CART_FILE.unlink()

    def save_pending_payment(self, token: str) -> None:
        data = {
            "token": token,
            "cart": [
                {"product_id": item.product.id, "quantity": item.quantity}
                for item in self.state.cart
            ],
        }

        PENDING_PAYMENT_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear_pending_payment(self) -> None:
        if PENDING_PAYMENT_FILE.exists():
            PENDING_PAYMENT_FILE.unlink()

    def cart_items_payload(self) -> list[dict]:
        return [
            {"product_id": item.product.id, "quantity": item.quantity}
            for item in self.state.cart
        ]

    async def refresh_cart_quote(self) -> None:
        self.cart_quote_box.controls.clear()

        if not self.state.cart:
            self.cart_quote = {}
            self.cart_quote_box.controls = [
                self.quote_row("Productos", "0"),
                self.quote_row("Subtotal", currency(0)),
                self.quote_row("Envío", currency(0)),
                self.quote_row("Total a pagar", currency(0), True),
            ]
            self.page.update()
            return

        # Si no hay sesión, mostramos total local sin descuentos
        if not self.state.current_user:
            subtotal = int(self.state.cart_subtotal)
            shipping = int(self.state.shipping_cost)
            total = int(self.state.checkout_total)

            self.cart_quote = {
                "subtotal": subtotal,
                "shipping": shipping,
                "preference_discount": 0,
                "points_discount": 0,
                "total": total,
            }

            self.cart_quote_box.controls = [
                self.quote_row("Productos", str(self.state.cart_count)),
                self.quote_row("Subtotal", currency(subtotal)),
                self.quote_row("Envío", currency(shipping)),
                self.quote_row("Descuento preferencias", f"-{currency(0)}"),
                self.quote_row("Descuento puntos", f"-{currency(0)}"),
                ft.Text(
                    "Inicia sesión para aplicar puntos y descuentos.",
                    color=IschuuColors.TEXT_MUTED,
                    size=12,
                ),
                self.quote_row("Total a pagar", currency(total), True),
            ]

            self.page.update()
            return

        try:
            self.cart_quote = await self.api.quote_cart_payment(
                self.cart_items_payload(),
                use_points=bool(self.use_points_switch.value),
            )

            subtotal = int(self.cart_quote.get("subtotal", 0))
            shipping = int(self.cart_quote.get("shipping", 0))
            preference_discount = int(self.cart_quote.get("preference_discount", 0))
            points_discount = int(self.cart_quote.get("points_discount", 0))
            total = int(self.cart_quote.get("total", 0))

            points_to_spend = int(self.cart_quote.get("points_to_spend", 0))
            points_label = self.cart_quote.get("points_discount_label", "")

            self.cart_quote_box.controls = [
                self.quote_row("Productos", str(self.state.cart_count)),
                self.quote_row("Subtotal", currency(subtotal)),
                self.quote_row("Envío", currency(shipping)),
                self.quote_row(
                    "Descuento preferencias",
                    f"-{currency(preference_discount)}",
                ),
                self.quote_row(
                    "Descuento puntos",
                    f"-{currency(points_discount)}",
                ),
            ]

            if bool(self.use_points_switch.value):
                if points_to_spend > 0:
                    self.cart_quote_box.controls.append(
                        ft.Text(
                            points_label or f"Usaste {points_to_spend} puntos.",
                            color=IschuuColors.TEXT_MUTED,
                            size=12,
                        )
                    )
                else:
                    self.cart_quote_box.controls.append(
                        ft.Text(
                            "No tienes puntos disponibles para aplicar.",
                            color=IschuuColors.TEXT_MUTED,
                            size=12,
                        )
                    )
            else:
                self.cart_quote_box.controls.append(
                    ft.Text(
                        "Activa el switch para usar tus puntos disponibles.",
                        color=IschuuColors.TEXT_MUTED,
                        size=12,
                    )
                )

            self.cart_quote_box.controls.append(
                self.quote_row(
                    "Total a pagar",
                    currency(total),
                    True,
                )
            )

        except Exception as exc:
            subtotal = int(self.state.cart_subtotal)
            shipping = int(self.state.shipping_cost)
            total = int(self.state.checkout_total)

            self.cart_quote_box.controls = [
                self.quote_row("Productos", str(self.state.cart_count)),
                self.quote_row("Subtotal", currency(subtotal)),
                self.quote_row("Envío", currency(shipping)),
                self.quote_row("Descuento preferencias", f"-{currency(0)}"),
                self.quote_row("Descuento puntos", f"-{currency(0)}"),
                self.quote_row("Total a pagar", currency(total), True),
                ft.Text(
                    "No se pudo calcular descuentos desde el backend.",
                    color=IschuuColors.TEXT_MUTED,
                    size=12,
                ),
            ]

            self.show_message(
                f"No se pudo calcular descuento: {exc}",
                error=True,
            )

        self.page.update()

    def quote_row(self, label: str, value: str, highlight: bool = False) -> ft.Control:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    label,
                    color=IschuuColors.TEXT if highlight else IschuuColors.TEXT_MUTED,
                ),
                ft.Text(
                    value,
                    weight=ft.FontWeight.BOLD,
                    color=IschuuColors.VANILLA if highlight else IschuuColors.TEXT,
                ),
            ],
        )

    async def handle_login(self, email: str, password: str) -> None:
        try:
            data = await self.api.login(email, password)
            self.api.set_token(data["access_token"])

            user_data = data["user"]
            self.state.current_user = self.user_from_dict(user_data)

            self.apply_shipping_address_to_fields(
                getattr(self.state.current_user, "shipping_address", {}) or {}
            )

            await self.load_orders()
            await self.check_pending_payment(show_if_empty=False)

            if self.is_admin():
                await self.load_admin_data()

            self.navbar = build_navigation_bar(self)
            self.page.navigation_bar = self.navbar

            self.show_message("Sesión iniciada correctamente")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo iniciar sesión: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo iniciar sesión: {exc}", error=True)

    async def handle_register(self, name: str, email: str, password: str) -> None:
        try:
            if not name.strip():
                self.show_message("Ingresa un nombre para registrarte.", error=True)
                return

            await self.api.register(name, email, password)
            await self.handle_login(email, password)

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo registrar: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo registrar: {exc}", error=True)

    async def handle_forgot_password(self, email: str) -> None:
        try:
            if not email.strip():
                self.show_message("Ingresa tu correo.", error=True)
                return

            await self.api.forgot_password(email)
            self.show_message("Si la cuenta existe, recibirás un token por correo.")

            self.auth_mode = "reset"
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo recuperar contraseña: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo recuperar contraseña: {exc}", error=True)

    async def handle_reset_password(self, token: str, new_password: str) -> None:
        try:
            await self.api.reset_password(token, new_password)
            self.auth_mode = "login"
            self.show_message("Contraseña actualizada correctamente.")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo cambiar contraseña: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo cambiar contraseña: {exc}", error=True)

    def handle_logout(self) -> None:
        self.run_async(self.disconnect_push_user())
        self.state.current_user = None
        self.state.orders = []
        self.admin_summary = {}
        self.admin_users = []
        self.admin_products = []
        self.admin_orders = []
        self.admin_settings = {}

        self.api.set_token(None)

        self.current_section = 3
        self.navbar = build_navigation_bar(self)
        self.page.navigation_bar = self.navbar

        self.show_message("Sesión cerrada. Tu carrito se mantiene guardado.")
        self.render()

    def handle_add_to_cart(self, product_id: str) -> None:
        product = next((p for p in self.state.products if p.id == product_id), None)

        if not product:
            self.show_message("Producto no encontrado.", error=True)
            return

        if int(product.stock) <= 0:
            self.show_message("Este producto no tiene stock disponible.", error=True)
            return

        item = next((x for x in self.state.cart if x.product.id == product_id), None)

        if item:
            if item.quantity >= product.stock:
                self.show_message("No puedes superar el stock disponible.", error=True)
                return

            item.quantity += 1

        else:
            self.state.cart.append(CartItem(product=product, quantity=1))

        self.save_cart_to_file()
        self.show_message("Artículo añadido al carrito")
        self.render()
        self.run_async(self.refresh_cart_quote())

    def handle_change_quantity(self, product_id: str, delta: int) -> None:
        item = next(
            (cart_item for cart_item in self.state.cart if cart_item.product.id == product_id),
            None,
        )

        if not item:
            return

        new_quantity = item.quantity + delta

        if new_quantity <= 0:
            self.state.cart = [
                cart_item
                for cart_item in self.state.cart
                if cart_item.product.id != product_id
            ]

        elif new_quantity > item.product.stock:
            self.show_message("Cantidad superior al stock disponible.", error=True)
            return

        else:
            item.quantity = new_quantity

        self.save_cart_to_file()
        self.render()
        self.run_async(self.refresh_cart_quote())

    def handle_remove_from_cart(self, product_id: str) -> None:
        self.state.cart = [
            cart_item
            for cart_item in self.state.cart
            if cart_item.product.id != product_id
        ]

        self.save_cart_to_file()
        self.show_message("Producto eliminado del carrito.")
        self.render()
        self.run_async(self.refresh_cart_quote())

    async def handle_checkout(self) -> None:
        if not self.state.current_user:
            self.show_message("Debes iniciar sesión desde Perfil para pagar.", error=True)
            self.current_section = 3
            self.render()
            return

        if not self.state.cart:
            self.show_message("Tu carrito está vacío.", error=True)
            return

        try:
            shipping_address = self.shipping_address_payload()

            if not self.shipping_address_is_complete():
                self.shipping_address_editing = True
                self.shipping_address_saved = False
                self.show_message(
                    "Debes ingresar una dirección de despacho antes de pagar.",
                    error=True,
                )
                self.render()
                return

            shipping_address = self.shipping_address_payload()

            data = await self.api.create_cart_payment(
                self.cart_items_payload(),
                use_points=bool(self.use_points_switch.value),
                shipping_address=shipping_address,
            )

            self.save_pending_payment(data["token"])
            await self.page.launch_url(data["redirect_url"])

            self.show_message(
                "Pago iniciado. La app verificará automáticamente el resultado."
            )

            self.run_async(self.monitor_pending_payment())

        except Exception as exc:
            self.show_message(f"No se pudo iniciar Webpay: {exc}", error=True)

    async def check_pending_payment(self, show_if_empty: bool = True) -> None:
        if not self.state.current_user:
            if show_if_empty:
                self.show_message("Debes iniciar sesión para verificar el pago.", error=True)
            return

        if not PENDING_PAYMENT_FILE.exists():
            if show_if_empty:
                self.show_message("No hay pagos pendientes por verificar.", error=True)
            return

        try:
            data = json.loads(PENDING_PAYMENT_FILE.read_text(encoding="utf-8"))
            token = data.get("token")

            if not token:
                if show_if_empty:
                    self.show_message("No se encontró token de pago pendiente.", error=True)
                return

            payment_status = await self.api.get_payment_status(token)
            status = str(payment_status.get("status", "")).upper()
            order_created = bool(payment_status.get("order_created", False))
            requires_review = bool(payment_status.get("requires_manual_review", False))

            if requires_review:
                self.clear_pending_payment()
                detail = payment_status.get("fulfillment_error", "El pago requiere revisión manual.")
                self.show_message(f"Pago recibido, pero el pedido requiere revisión: {detail}", error=True)
                return

            if status == "AUTHORIZED" and order_created:
                self.clear_cart_file()
                self.clear_pending_payment()
                await self.load_orders()
                await self.refresh_me()
                self.current_section = 2
                self.show_message("Pago confirmado. El pedido pasó a Seguimiento.")
                self.render()
                return

            if status in ["FAILED", "REJECTED", "NULLIFIED"]:
                self.clear_pending_payment()
                self.show_message("El pago fue rechazado o cancelado. El carrito se mantiene.", error=True)
                return

            if show_if_empty:
                self.show_message(f"El pago aún no está confirmado. Estado actual: {status}")

        except Exception as exc:
            if show_if_empty:
                self.show_message(f"No se pudo verificar el pago: {exc}", error=True)

    async def monitor_pending_payment(self) -> None:
        if self.payment_polling:
            return

        self.payment_polling = True

        try:
            attempts = 0
            max_attempts = 60

            while attempts < max_attempts:
                attempts += 1

                if not PENDING_PAYMENT_FILE.exists():
                    break

                await self.check_pending_payment(show_if_empty=False)

                if not PENDING_PAYMENT_FILE.exists():
                    break

                await asyncio.sleep(3)

        finally:
            self.payment_polling = False

    async def load_admin_data(self) -> None:
        if not self.is_admin():
            return

        self.admin_summary = await self.api.admin_get_summary()
        self.admin_users = await self.api.admin_get_users()
        self.admin_products = await self.api.admin_get_products()
        self.admin_orders = await self.api.admin_get_orders()

        try:
            self.admin_settings = await self.api.admin_get_settings()
        except Exception:
            self.admin_settings = {}

    async def admin_create_product(self, payload: dict, image_path: str = "") -> None:
        try:
            if image_path:
                uploaded = await self.api.admin_upload_product_image(image_path)
                payload["image_url"] = uploaded["image_url"]

            await self.api.admin_create_product(payload)
            await self.load_admin_data()
            await self.load_products()
            self.refresh_product_list()
            self.show_message("Producto creado correctamente")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo crear producto: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo crear producto: {exc}", error=True)

    async def admin_delete_product(self, product_id: str) -> None:
        try:
            await self.api.admin_delete_product(product_id)
            await self.load_admin_data()
            await self.load_products()
            self.refresh_product_list()
            self.show_message("Producto eliminado correctamente")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo eliminar producto: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo eliminar producto: {exc}", error=True)

    async def admin_update_stock(
        self,
        product_id: str,
        operation: str,
        quantity: int | None = None,
        stock: int | None = None,
    ) -> None:
        try:
            await self.api.admin_update_stock(
                product_id,
                operation,
                quantity=quantity,
                stock=stock,
            )

            await self.load_admin_data()
            await self.load_products()
            self.refresh_product_list()

            self.show_message("Stock actualizado correctamente")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo actualizar stock: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo actualizar stock: {exc}", error=True)

    async def admin_update_order_status(self, order_id: str, status: str) -> None:
        try:
            await self.api.admin_update_order_status(order_id, status)
            await self.load_admin_data()

            self.show_message("Estado del pedido actualizado")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo actualizar pedido: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo actualizar pedido: {exc}", error=True)

    async def admin_update_user(
        self,
        user_id: str,
        is_active: bool,
        is_admin: bool,
        points: int,
    ) -> None:
        try:
            await self.api.admin_update_user(
                user_id,
                is_active=is_active,
                is_admin=is_admin,
                points=points,
            )

            await self.load_admin_data()

            self.show_message("Usuario actualizado correctamente")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo actualizar usuario: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo actualizar usuario: {exc}", error=True)

    async def admin_update_settings(self, payload: dict) -> None:
        try:
            await self.api.admin_update_settings(payload)
            await self.load_admin_data()
            self.show_message("Configuración actualizada")
            self.render()

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo actualizar configuración: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo actualizar configuración: {exc}", error=True)

    async def admin_export_orders(self) -> None:
        try:
            output_path = "pedidos_ischuu.xlsx"
            await self.api.admin_export_orders(output_path)
            self.show_message(f"Pedidos exportados en {output_path}")

        except httpx.HTTPStatusError as exc:
            self.show_message(f"No se pudo exportar: {exc.response.text}", error=True)

        except Exception as exc:
            self.show_message(f"No se pudo exportar: {exc}", error=True)

    def on_search(self, e) -> None:
        self.state.search_text = e.control.value or ""
        self.refresh_product_list()
        self.page.update()

    def on_category_change(self, e) -> None:
        self.state.category_filter = e.control.value or "Todas"
        self.refresh_product_list()
        self.page.update()

    def on_nav_change(self, e) -> None:
        selected_index = int(e.control.selected_index)

        max_index = 5 if self.is_admin() else 4

        if selected_index < 0 or selected_index > max_index:
            self.current_section = 0
        else:
            self.current_section = selected_index

        if self.current_section == 1:
            self.run_async(self.refresh_cart_quote())

        elif self.current_section == 2:
            if self.state.current_user:
                self.run_async(self.load_orders())

        elif self.current_section == 3:
            if self.state.current_user:
                self.run_async(self.refresh_me())

        elif self.current_section == 5:
            if self.is_admin():
                self.run_async(self.load_admin_data())
            else:
                self.current_section = 0

        self.render()
