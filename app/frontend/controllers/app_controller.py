from __future__ import annotations

import asyncio
import json
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

PREF_CART = "ischuu.cart"
PREF_PENDING_PAYMENT = "ischuu.pending_payment"
PREF_ACCESS_TOKEN = "ischuu.auth.access_token"
PREF_REFRESH_TOKEN = "ischuu.auth.refresh_token"

CHILE_REGIONS = [
    "Región de Arica y Parinacota",
    "Región de Tarapacá",
    "Región de Antofagasta",
    "Región de Atacama",
    "Región de Coquimbo",
    "Región de Valparaíso",
    "Región Metropolitana",
    "Región del Libertador General Bernardo O'Higgins",
    "Región del Maule",
    "Región de Ñuble",
    "Región del Biobío",
    "Región de La Araucanía",
    "Región de Los Ríos",
    "Región de Los Lagos",
    "Región de Aysén del General Carlos Ibáñez del Campo",
    "Región de Magallanes y de la Antártica Chilena",
]


class AppController:
    def __init__(self, page: ft.Page, api_base_url: str) -> None:
        self.page = page
        self.api = ApiClient(api_base_url)
        self.state = AppState()
        self.preferences = ft.SharedPreferences()
        self.page.services.append(self.preferences)
        self.url_launcher = ft.UrlLauncher()
        self.page.services.append(self.url_launcher)
        self.page.on_app_lifecycle_state_change = self.on_app_lifecycle_state_change
        self.is_light_theme = True
        apply_palette(self.is_light_theme)
        self.onesignal = None
        self.push_service_ready = False
        self.push_permission_granted = False
        self.push_status_message = "Preparando notificaciones móviles..."
        self.pending_push_route: str | None = None

        # Dirección de despacho
        self.shipping_address_saved = False
        self.shipping_address_editing = True

        self.current_section = 0
        self.auth_mode = "login"
        self.auth_feedback = ""
        self.auth_feedback_error = False
        self.auth_busy = False
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
            keyboard_type=ft.KeyboardType.PHONE,
            input_filter=ft.NumbersOnlyInputFilter(),
            max_length=12,
            **input_style(),
        )

        self.shipping_region = ft.Dropdown(
            label="Región",
            value="Región Metropolitana",
            options=[ft.dropdown.Option(region) for region in CHILE_REGIONS],
            enable_search=True,
            menu_height=360,
            filled=True,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
            label_style=ft.TextStyle(color=IschuuColors.TEXT_MUTED),
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
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
            max_length=8,
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
        self.page.padding = 10
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

        self.catalog_page_size_dropdown = ft.Dropdown(
            label="Productos por página",
            value=str(self.state.product_page_size),
            options=[
                ft.dropdown.Option("10"),
                ft.dropdown.Option("20"),
                ft.dropdown.Option("30"),
                ft.dropdown.Option("50"),
            ],
            on_select=self.on_catalog_page_size_change,
            width=190,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
        )

        self.admin_order_search = ft.TextField(
            label="Buscar pedido",
            hint_text="ID, cliente, correo, estado o producto",
            prefix_icon=ft.Icons.SEARCH,
            **input_style(),
        )
        self.admin_order_status_filter = ft.Dropdown(
            label="Estado",
            value="Todos",
            options=[ft.dropdown.Option("Todos")],
            width=190,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
        )
        self.admin_order_payment_filter = ft.Dropdown(
            label="Medio de pago",
            value="Todos",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Webpay"),
            ],
            width=190,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
        )
        self.admin_order_product_filter = ft.TextField(
            label="Producto",
            prefix_icon=ft.Icons.INVENTORY_2_OUTLINED,
            **input_style(),
        )
        self.admin_order_category_filter = ft.TextField(
            label="Categoría producto",
            prefix_icon=ft.Icons.CATEGORY_OUTLINED,
            **input_style(),
        )
        self.admin_order_date_filter = ft.TextField(
            label="Fecha exacta",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.EVENT_OUTLINED,
            width=190,
            **input_style(),
        )
        self.admin_order_start_date_filter = ft.TextField(
            label="Desde",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.DATE_RANGE_OUTLINED,
            width=190,
            **input_style(),
        )
        self.admin_order_end_date_filter = ft.TextField(
            label="Hasta",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.DATE_RANGE_OUTLINED,
            width=190,
            **input_style(),
        )
        self.admin_order_period_filter = ft.Dropdown(
            label="Periodo",
            value="",
            options=[
                ft.dropdown.Option(key="", text="Manual"),
                ft.dropdown.Option("today", "Hoy"),
                ft.dropdown.Option("week", "Semana actual"),
                ft.dropdown.Option("month", "Mes actual"),
                ft.dropdown.Option("year", "Año"),
            ],
            width=190,
            bgcolor=IschuuColors.SURFACE_ALT,
            color=IschuuColors.TEXT,
            border_color=IschuuColors.BORDER,
            focused_border_color=IschuuColors.PRIMARY_STRONG,
            border_radius=14,
        )
        self.admin_order_year_filter = ft.TextField(
            label="Año",
            hint_text="2026",
            prefix_icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
            width=140,
            **input_style(),
        )
        self.admin_orders_meta: dict[str, Any] = {
            "page": 1,
            "page_size": 20,
            "total": 0,
            "total_pages": 1,
        }

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
            self.shipping_comuna,
            self.shipping_street,
            self.shipping_number,
            self.shipping_details,
            self.search_field,
            self.admin_order_search,
            self.admin_order_product_filter,
            self.admin_order_category_filter,
            self.admin_order_date_filter,
            self.admin_order_start_date_filter,
            self.admin_order_end_date_filter,
            self.admin_order_year_filter,
        ]

        for text_field in text_fields:
            for property_name, value in text_field_style.items():
                setattr(text_field, property_name, value)

        self.category_dropdown.bgcolor = IschuuColors.SURFACE_ALT
        self.category_dropdown.color = IschuuColors.TEXT
        self.category_dropdown.border_color = IschuuColors.BORDER
        self.category_dropdown.focused_border_color = IschuuColors.PRIMARY_STRONG
        self.category_dropdown.label_style = ft.TextStyle(color=IschuuColors.TEXT_MUTED)

        for dropdown in [
            self.catalog_page_size_dropdown,
            self.admin_order_status_filter,
            self.admin_order_payment_filter,
            self.admin_order_period_filter,
        ]:
            dropdown.bgcolor = IschuuColors.SURFACE_ALT
            dropdown.color = IschuuColors.TEXT
            dropdown.border_color = IschuuColors.BORDER
            dropdown.focused_border_color = IschuuColors.PRIMARY_STRONG
            dropdown.label_style = ft.TextStyle(color=IschuuColors.TEXT_MUTED)

        self.shipping_region.bgcolor = IschuuColors.SURFACE_ALT
        self.shipping_region.color = IschuuColors.TEXT
        self.shipping_region.border_color = IschuuColors.BORDER
        self.shipping_region.focused_border_color = IschuuColors.PRIMARY_STRONG
        self.shipping_region.label_style = ft.TextStyle(color=IschuuColors.TEXT_MUTED)

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
        self.push_status_message = "Notificación recibida correctamente."
        if self.state.current_user is not None:
            self.run_async(self.load_orders())

    def on_push_permission_change(self, event) -> None:
        self.push_permission_granted = bool(getattr(event, "permission", False))
        self.push_status_message = (
            "Notificaciones activas en este teléfono."
            if self.push_permission_granted
            else "Android no tiene permiso para mostrar notificaciones."
        )
        if self.state.current_user is not None:
            self.render()

    def on_push_error(self, event) -> None:
        message = str(getattr(event, "message", "Error desconocido")).strip()
        self.push_status_message = f"Error de notificaciones: {message}"
        print(self.push_status_message)

    async def setup_push_notifications(self) -> bool:
        if self.onesignal is not None:
            return True

        if not self._is_mobile_platform():
            return False

        try:
            config = await self.api.get_notification_config()
            app_id = str(config.get("app_id", "")).strip()
            if not config.get("enabled") or not app_id:
                self.push_status_message = "OneSignal no está configurado en el backend."
                return False

            import flet_onesignal as fos

            self.onesignal = fos.OneSignal(
                app_id=app_id,
                log_level=fos.OSLogLevel.INFO,
                on_notification_click=self.on_push_notification_click,
                on_notification_foreground=self.on_push_notification_foreground,
                on_permission_change=self.on_push_permission_change,
                on_error=self.on_push_error,
            )
            self.page.services.append(self.onesignal)
            self.push_service_ready = True
            self.push_status_message = "OneSignal listo; falta vincular la cuenta."
            self.page.update()
            return True
        except Exception as exc:
            print(f"Notificaciones móviles no disponibles: {exc}")
            self.push_status_message = (
                "Este APK no incluye el servicio de notificaciones. Reinstala la versión corregida."
            )
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
                granted = await self.onesignal.notifications.get_permission()
                if (
                    not granted
                    and await self.onesignal.notifications.can_request_permission()
                ):
                    granted = await self.onesignal.notifications.request_permission(
                        fallback_to_settings=False
                    )
                self.push_permission_granted = bool(granted)
                if granted:
                    await self.onesignal.user.opt_in_push()
                    linked = False
                    for _attempt in range(6):
                        external_id = await self.onesignal.user.get_external_id()
                        opted_in = await self.onesignal.user.is_push_opted_in()
                        subscription_id = (
                            await self.onesignal.user.get_push_subscription_id()
                        )
                        linked = bool(
                            external_id == str(user.id)
                            and opted_in
                            and subscription_id
                        )
                        if linked:
                            break
                        await asyncio.sleep(0.5)

                    if linked:
                        self.push_status_message = "Notificaciones activas en este teléfono."
                    else:
                        self.push_status_message = (
                            "OneSignal aún está vinculando esta cuenta con el teléfono."
                        )
                else:
                    self.push_status_message = (
                        "Android no autorizó las notificaciones. Actívalas desde Guardar."
                    )
            else:
                await self.onesignal.user.opt_out_push()
                self.push_permission_granted = False
                self.push_status_message = "Notificaciones desactivadas desde el perfil."
        except Exception as exc:
            print(f"No se pudo vincular el teléfono a las notificaciones: {exc}")
            self.push_status_message = f"No se pudo vincular este teléfono: {exc}"

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

    def handle_test_notification(self) -> None:
        self.run_async(self.test_push_notification())

    async def test_push_notification(self) -> None:
        if self.state.current_user is None:
            self.show_message("Debes iniciar sesión para probar notificaciones.", error=True)
            return
        try:
            if self.onesignal is None and not await self.setup_push_notifications():
                raise RuntimeError(self.push_status_message)
            await self.activate_push_for_current_user()
            if not self.push_permission_granted:
                raise RuntimeError(self.push_status_message)
            await self.api.send_test_notification()
            self.show_message("Notificación de prueba enviada al teléfono.")
        except httpx.HTTPStatusError as exc:
            message = self.http_error_message(exc, "No se pudo enviar la notificación de prueba.")
            self.push_status_message = message
            self.show_message(message, error=True)
            self.render()
        except Exception as exc:
            self.push_status_message = str(exc)
            self.show_message(self.push_status_message, error=True)
            self.render()

    async def save_notification_preference(self, enabled: bool) -> None:
        try:
            effective_enabled = enabled

            if enabled and self.onesignal is None:
                effective_enabled = await self.setup_push_notifications()

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
                        opted_in = await self.onesignal.user.is_push_opted_in()
                        subscription_id = await self.onesignal.user.get_push_subscription_id()
                        effective_enabled = bool(opted_in and subscription_id)
                        self.push_status_message = (
                            "Notificaciones activas en este teléfono."
                            if effective_enabled
                            else "OneSignal aún no asignó una suscripción al teléfono."
                        )
                else:
                    await self.onesignal.user.opt_out_push()
                    self.push_permission_granted = False
                    self.push_status_message = "Notificaciones desactivadas desde el perfil."

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
        url = f"https://wa.me/{phone}?text={quote(message, safe='')}"

        self.run_async(self.launch_external_url(url, "WhatsApp"))

    def open_help_email(self) -> None:
        email = "soporte@ischuu.cl"
        subject = "Solicitud de ayuda - Ischuu"
        body = "Hola, necesito ayuda con la aplicación Ischuu."

        url = (
            f"mailto:{email}?subject={quote(subject, safe='')}"
            f"&body={quote(body, safe='')}"
        )
        self.run_async(self.launch_external_url(url, "correo"))

    async def launch_external_url(self, url: str, channel: str) -> None:
        try:
            await self.url_launcher.launch_url(
                url,
                mode=ft.LaunchMode.EXTERNAL_APPLICATION,
            )
        except Exception as exc:
            print(f"No se pudo abrir {channel}: {exc}")
            self.show_message(
                f"No se encontró una aplicación para abrir {channel}.",
                error=True,
            )

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

    def shipping_address_validation_message(self) -> str:
        data = self.shipping_address_payload()
        labels = {
            "recipient": "Nombre de quien recibe",
            "phone": "Teléfono de contacto",
            "region": "Ciudad o región",
            "comuna": "Comuna",
            "street": "Calle o dirección",
            "number": "Número",
        }
        missing = [
            label
            for field, label in labels.items()
            if not str(data.get(field, "")).strip()
        ]
        if missing:
            return f"Faltan datos de despacho: {', '.join(missing)}."

        phone = str(data.get("phone", "")).strip()
        number = str(data.get("number", "")).strip()
        if not phone.isdigit():
            return "El teléfono de contacto debe contener solamente números."
        if not number.isdigit():
            return "El número de la dirección debe contener solamente números."

        return ""

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

    def set_auth_feedback(self, message: str = "", error: bool = False) -> None:
        self.auth_feedback = message
        self.auth_feedback_error = error

    @staticmethod
    def http_error_message(exc: httpx.HTTPStatusError, fallback: str) -> str:
        try:
            detail = exc.response.json().get("detail")
            if isinstance(detail, list):
                messages = [str(item.get("msg", "Dato inválido")) for item in detail]
                return "; ".join(messages)
            if detail:
                return str(detail)
        except Exception:
            pass
        return fallback

    def user_from_dict(self, user_data: dict) -> User:
        return User(
            id=user_data.get("id", ""),
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            points=int(user_data.get("points", 0)),
            preferences=user_data.get("preferences", {}) or {},
            favorite_categories=user_data.get("favorite_categories", []),
            preference_stats=user_data.get("preference_stats", {}) or {},
            notifications_enabled=bool(user_data.get("notifications_enabled", True)),
            is_admin=bool(user_data.get("is_admin", False)),
            is_active=bool(user_data.get("is_active", True)),
            shipping_address=user_data.get("shipping_address", {}) or {},
        )

    def product_from_dict(self, data: dict) -> Product:
        return Product(
            id=data["id"],
            name=data["name"],
            series=data.get("series", ""),
            price=int(data.get("price", 0)),
            stock=int(data.get("stock", 0)),
            category=data.get("category", "General"),
            rarity=data.get("rarity", "Común"),
            description=data.get("description", ""),
            is_original=bool(data.get("is_original", True)),
            image=data.get("image_url", ""),
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
        # La dirección se guarda en el backend asociada al usuario.
        # Se mantiene este método por compatibilidad con llamadas antiguas.
        return

    def load_shipping_address_from_file(self) -> None:
        # La dirección se carga desde /auth/me al iniciar sesión.
        self.shipping_address_saved = self.shipping_address_is_complete()
        self.shipping_address_editing = not self.shipping_address_saved

    async def handle_save_shipping_address(self) -> None:
        if not self.state.current_user:
            self.show_message(
                "Debes iniciar sesión para guardar la dirección.",
                error=True,
            )
            return

        validation_message = self.shipping_address_validation_message()
        if validation_message:
            self.show_message(
                validation_message,
                error=True,
            )
            return

        try:
            updated_user = await self.api.update_my_shipping_address(
                self.shipping_address_payload()
            )
            self.state.current_user = self.user_from_dict(updated_user)
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

    async def persist_session(
        self,
        access_token: str,
        refresh_token: str | None = None,
    ) -> None:
        await self.preferences.set(PREF_ACCESS_TOKEN, access_token)
        if refresh_token:
            await self.preferences.set(PREF_REFRESH_TOKEN, refresh_token)
        else:
            await self.preferences.remove(PREF_REFRESH_TOKEN)

    async def clear_persisted_session(self) -> None:
        await self.preferences.remove(PREF_ACCESS_TOKEN)
        await self.preferences.remove(PREF_REFRESH_TOKEN)

    async def apply_authenticated_user(self, user_data: dict) -> None:
        self.state.current_user = self.user_from_dict(user_data)
        self.apply_shipping_address_to_fields(
            getattr(self.state.current_user, "shipping_address", {}) or {}
        )
        await self.activate_push_for_current_user()
        await self.load_orders()
        await self.check_pending_payment(show_if_empty=False)

        if self.is_admin():
            await self.load_admin_data()

        self.navbar = build_navigation_bar(self)
        self.page.navigation_bar = self.navbar

    async def restore_session(self) -> bool:
        access_value = await self.preferences.get(PREF_ACCESS_TOKEN)
        refresh_value = await self.preferences.get(PREF_REFRESH_TOKEN)
        access_token = str(access_value or "").strip()
        refresh_token = str(refresh_value or "").strip()

        if not access_token and not refresh_token:
            return False

        user_data: dict | None = None
        if access_token:
            self.api.set_token(access_token)
            try:
                user_data = await self.api.get_me()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    await self.clear_persisted_session()
                    await self.disconnect_push_user()
                    self.api.set_token(None)
                    self.show_message(
                        self.http_error_message(exc, "Tu cuenta no está activa."),
                        error=True,
                    )
                    return False
                if exc.response.status_code != 401:
                    raise

        if user_data is None and refresh_token:
            try:
                refreshed = await self.api.refresh_session(refresh_token)
                access_token = str(refreshed["access_token"])
                refresh_token = str(refreshed.get("refresh_token", refresh_token))
                self.api.set_token(access_token)
                await self.persist_session(access_token, refresh_token)
                user_data = refreshed["user"]
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {400, 401, 403, 404, 422}:
                    await self.clear_persisted_session()
                    await self.disconnect_push_user()
                    self.api.set_token(None)
                    return False
                raise

        if user_data is None:
            await self.clear_persisted_session()
            self.api.set_token(None)
            return False

        await self.apply_authenticated_user(user_data)
        return True

    async def startup_load(self) -> None:
        await self.setup_push_notifications()

        try:
            await self.load_products()
            await self.load_cart_from_file()
            self.load_shipping_address_from_file()
            self.refresh_product_list()
        except Exception as exc:
            self.show_message(f"No se pudo cargar catálogo: {exc}", error=True)

        try:
            await self.restore_session()
        except (httpx.RequestError, TimeoutError) as exc:
            print(f"No se pudo restaurar la sesión por un problema de red: {exc}")
            self.push_status_message = (
                "La sesión sigue guardada; se restaurará cuando vuelva la conexión."
            )
        except Exception as exc:
            print(f"No se pudo restaurar la sesión: {exc}")

        self.render()

    async def load_products(self, page: int | None = None) -> None:
        if page is not None:
            self.state.product_page = max(1, int(page))

        data = await self.api.get_products(
            search=self.state.search_text,
            category=self.state.category_filter,
            page=self.state.product_page,
            page_size=self.state.product_page_size,
        )
        if isinstance(data, list):
            data = {
                "items": data,
                "page": 1,
                "page_size": len(data) or self.state.product_page_size,
                "total": len(data),
                "total_pages": 1,
                "categories": [],
            }
        items = data.get("items", [])
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
            for p in items
        ]
        self.state.product_page = int(data.get("page", self.state.product_page))
        self.state.product_page_size = int(data.get("page_size", self.state.product_page_size))
        self.state.product_total = int(data.get("total", len(items)))
        self.state.product_total_pages = max(1, int(data.get("total_pages", 1)))
        self.state.product_categories = data.get("categories", []) or []

        self.category_dropdown.options = [
            ft.dropdown.Option(category)
            for category in self.state.categories
        ]
        self.category_dropdown.value = self.state.category_filter
        self.catalog_page_size_dropdown.value = str(self.state.product_page_size)

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

    async def reload_catalog(self, page: int | None = None) -> None:
        await self.load_products(page=page)
        self.refresh_product_list()
        self.render()

    def set_catalog_page(self, page: int) -> None:
        page = max(1, min(int(page), int(self.state.product_total_pages or 1)))
        if page == self.state.product_page:
            return
        self.run_async(self.reload_catalog(page=page))

    def on_catalog_page_size_change(self, e) -> None:
        try:
            self.state.product_page_size = int(e.control.value or 10)
        except ValueError:
            self.state.product_page_size = 10
        self.state.product_page = 1
        self.run_async(self.reload_catalog(page=1))

    def admin_order_filters(self, page: int | None = None) -> dict:
        year_value = str(self.admin_order_year_filter.value or "").strip()
        filters = {
            "search": self.admin_order_search.value or "",
            "status": self.admin_order_status_filter.value or "",
            "payment_method": self.admin_order_payment_filter.value or "",
            "product": self.admin_order_product_filter.value or "",
            "category": self.admin_order_category_filter.value or "",
            "date": self.admin_order_date_filter.value or "",
            "start_date": self.admin_order_start_date_filter.value or "",
            "end_date": self.admin_order_end_date_filter.value or "",
            "period": self.admin_order_period_filter.value or "",
            "page": page or self.admin_orders_meta.get("page", 1),
            "page_size": self.admin_orders_meta.get("page_size", 20),
        }
        if year_value:
            filters["year"] = year_value
        return filters

    async def load_admin_orders(self, page: int | None = None) -> None:
        data = await self.api.admin_get_orders(self.admin_order_filters(page=page))
        self.admin_orders = data.get("items", [])
        self.admin_orders_meta = {
            "page": int(data.get("page", 1)),
            "page_size": int(data.get("page_size", 20)),
            "total": int(data.get("total", len(self.admin_orders))),
            "total_pages": max(1, int(data.get("total_pages", 1))),
        }

    async def reload_admin_orders(self, page: int | None = None) -> None:
        await self.load_admin_orders(page=page or 1)
        self.render()

    def apply_admin_order_filters(self) -> None:
        self.admin_orders_meta["page"] = 1
        self.run_async(self.reload_admin_orders(page=1))

    def clear_admin_order_filters(self) -> None:
        self.admin_order_search.value = ""
        self.admin_order_status_filter.value = "Todos"
        self.admin_order_payment_filter.value = "Todos"
        self.admin_order_product_filter.value = ""
        self.admin_order_category_filter.value = ""
        self.admin_order_date_filter.value = ""
        self.admin_order_start_date_filter.value = ""
        self.admin_order_end_date_filter.value = ""
        self.admin_order_period_filter.value = ""
        self.admin_order_year_filter.value = ""
        self.admin_orders_meta["page"] = 1
        self.run_async(self.reload_admin_orders(page=1))

    def set_admin_orders_page(self, page: int) -> None:
        page = max(1, min(int(page), int(self.admin_orders_meta.get("total_pages", 1))))
        if page == int(self.admin_orders_meta.get("page", 1)):
            return
        self.run_async(self.reload_admin_orders(page=page))

    def save_cart_to_file(self) -> None:
        self.run_async(self._save_cart_to_preferences())

    async def _save_cart_to_preferences(self) -> None:
        data = [
            {"product_id": item.product.id, "quantity": item.quantity}
            for item in self.state.cart
        ]
        await self.preferences.set(PREF_CART, json.dumps(data, ensure_ascii=False))

    async def load_cart_from_file(self) -> None:
        try:
            raw = await self.preferences.get(PREF_CART)
            if not raw:
                return

            data = json.loads(str(raw))
            self.state.cart.clear()

            for row in data:
                product = next(
                    (p for p in self.state.products if p.id == row.get("product_id")),
                    None,
                )
                if product is None and row.get("product_id"):
                    try:
                        product = self.product_from_dict(
                            await self.api.get_product(str(row.get("product_id")))
                        )
                    except Exception:
                        product = None
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
        self.run_async(self.preferences.remove(PREF_CART))

    def save_pending_payment(self, token: str) -> None:
        data = {
            "token": token,
            "cart": [
                {"product_id": item.product.id, "quantity": item.quantity}
                for item in self.state.cart
            ],
        }
        self.run_async(
            self.preferences.set(
                PREF_PENDING_PAYMENT,
                json.dumps(data, ensure_ascii=False),
            )
        )

    def clear_pending_payment(self) -> None:
        self.run_async(self.preferences.remove(PREF_PENDING_PAYMENT))

    async def _get_pending_payment(self) -> dict | None:
        try:
            raw = await self.preferences.get(PREF_PENDING_PAYMENT)
            if not raw:
                return None
            value = json.loads(str(raw))
            return value if isinstance(value, dict) else None
        except Exception:
            return None

    def cart_items_payload(self) -> list[dict]:
        return [
            {"product_id": item.product.id, "quantity": item.quantity}
            for item in self.state.cart
        ]

    async def refresh_cart_products_from_backend(self) -> list[str]:
        warnings: list[str] = []

        for item in list(self.state.cart):
            try:
                product = self.product_from_dict(
                    await self.api.get_product(item.product.id)
                )
            except Exception:
                continue

            item.product = product
            if int(product.stock) <= 0:
                warnings.append(f"{product.name} está sin stock.")
            elif item.quantity > int(product.stock):
                item.quantity = int(product.stock)
                warnings.append(
                    f"{product.name} ahora tiene solo {product.stock} unidades disponibles."
                )

        if warnings:
            self.save_cart_to_file()

        return warnings

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
            message = (
                self.http_error_message(exc, "No se pudo calcular el total desde el backend.")
                if isinstance(exc, httpx.HTTPStatusError)
                else "No se pudo calcular el total desde el backend."
            )
            subtotal = int(self.state.cart_subtotal)
            shipping = int(self.state.shipping_cost)
            total = int(self.state.checkout_total)
            self.cart_quote = {}

            self.cart_quote_box.controls = [
                self.quote_row("Productos", str(self.state.cart_count)),
                self.quote_row("Subtotal", currency(subtotal)),
                self.quote_row("Envío", currency(shipping)),
                self.quote_row("Descuento preferencias", f"-{currency(0)}"),
                self.quote_row("Descuento puntos", f"-{currency(0)}"),
                self.quote_row("Total a pagar", currency(total), True),
                ft.Text(
                    message,
                    color=IschuuColors.DANGER,
                    size=12,
                ),
            ]

            self.show_message(
                message,
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

    async def handle_login(
        self,
        email: str,
        password: str,
        success_message: str = "Sesión iniciada correctamente",
    ) -> bool:
        email = email.lower().strip()
        if not email or not password:
            self.set_auth_feedback("Ingresa correo y contraseña.", error=True)
            self.render()
            return False

        try:
            self.set_auth_feedback()
            data = await self.api.login(email, password)
            self.api.set_token(data["access_token"])
            await self.persist_session(
                str(data["access_token"]),
                str(data.get("refresh_token", "")) or None,
            )
            await self.apply_authenticated_user(data["user"])
            self.auth_mode = "login"

            self.show_message(success_message)
            self.render()
            return True

        except httpx.HTTPStatusError as exc:
            message = self.http_error_message(exc, "No se pudo iniciar sesión.")
            self.set_auth_feedback(message, error=True)
            self.show_message(message, error=True)
            self.render()
            return False

        except Exception as exc:
            message = f"No se pudo conectar con Ischuu: {exc}"
            self.set_auth_feedback(message, error=True)
            self.show_message(message, error=True)
            self.render()
            return False

    async def handle_register(self, name: str, email: str, password: str) -> None:
        if self.auth_busy:
            return

        name = name.strip()
        email = email.lower().strip()

        if len(name) < 2:
            self.set_auth_feedback("El nombre debe tener al menos 2 caracteres.", error=True)
            self.render()
            return
        if "@" not in email or "." not in email.partition("@")[2]:
            self.set_auth_feedback("Ingresa un correo válido.", error=True)
            self.render()
            return
        if len(password) < 6:
            self.set_auth_feedback("La contraseña debe tener al menos 6 caracteres.", error=True)
            self.render()
            return

        self.auth_busy = True
        try:
            self.set_auth_feedback("Creando cuenta...")
            self.render()
            await self.api.register(name, email, password)
            logged_in = await self.handle_login(
                email,
                password,
                success_message="Cuenta creada y sesión iniciada correctamente",
            )
            if not logged_in:
                self.auth_mode = "login"
                self.set_auth_feedback(
                    "La cuenta fue creada. Ahora inicia sesión con tu correo y contraseña."
                )
                self.show_message("Cuenta creada correctamente")
                self.render()

        except httpx.HTTPStatusError as exc:
            message = self.http_error_message(exc, "No se pudo crear la cuenta.")
            self.set_auth_feedback(message, error=True)
            self.show_message(message, error=True)
            self.render()

        except Exception as exc:
            message = f"No se pudo conectar con Ischuu: {exc}"
            self.set_auth_feedback(message, error=True)
            self.show_message(message, error=True)
            self.render()
        finally:
            self.auth_busy = False
            if self.state.current_user is None:
                self.render()

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
        self.run_async(self.perform_logout())

    async def perform_logout(self) -> None:
        try:
            await self.disconnect_push_user()
        finally:
            try:
                await self.clear_persisted_session()
            except Exception as exc:
                print(f"No se pudo borrar la sesión guardada: {exc}")

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

        elif item.product.stock <= 0:
            self.show_message("Este producto quedó sin stock. Elimínalo del carrito para continuar.", error=True)
            return

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
            validation_message = self.shipping_address_validation_message()
            if validation_message:
                self.shipping_address_editing = True
                self.shipping_address_saved = False
                self.show_message(
                    "Antes de continuar con el pago, debes registrar una dirección de entrega. "
                    + validation_message,
                    error=True,
                )
                self.current_section = 1
                self.render()
                return

            stock_warnings = await self.refresh_cart_products_from_backend()
            if stock_warnings:
                self.show_message(stock_warnings[0], error=True)
                await self.refresh_cart_quote()
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

        except httpx.HTTPStatusError as exc:
            self.show_message(
                self.http_error_message(exc, "No se pudo iniciar Webpay."),
                error=True,
            )
        except Exception as exc:
            self.show_message(f"No se pudo iniciar Webpay: {exc}", error=True)

    async def check_pending_payment(self, show_if_empty: bool = True) -> None:
        if not self.state.current_user:
            if show_if_empty:
                self.show_message("Debes iniciar sesión para verificar el pago.", error=True)
            return

        data = await self._get_pending_payment()
        if not data:
            if show_if_empty:
                self.show_message("No hay pagos pendientes por verificar.", error=True)
            return

        try:
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

                if not await self._get_pending_payment():
                    break

                await self.check_pending_payment(show_if_empty=False)

                if not await self._get_pending_payment():
                    break

                await asyncio.sleep(3)

        finally:
            self.payment_polling = False

    async def on_app_lifecycle_state_change(self, e) -> None:
        state = str(getattr(e, "data", "") or "").lower()
        if "resume" in state:
            try:
                await self.restore_session()
            except Exception as exc:
                print(f"No se pudo actualizar la sesión al volver a la app: {exc}")
            await self.check_pending_payment(show_if_empty=False)

    async def load_admin_data(self) -> None:
        if not self.is_admin():
            return

        self.admin_summary = await self.api.admin_get_summary()
        self.admin_users = await self.api.admin_get_users()
        self.admin_products = await self.api.admin_get_products()
        statuses = self.admin_summary.get("statuses", []) or []
        self.admin_order_status_filter.options = [
            ft.dropdown.Option("Todos"),
            *[ft.dropdown.Option(status) for status in statuses],
        ]
        await self.load_admin_orders(page=int(self.admin_orders_meta.get("page", 1)))

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
        self.state.product_page = 1
        self.run_async(self.reload_catalog(page=1))

    def on_category_change(self, e) -> None:
        self.state.category_filter = e.control.value or "Todas"
        self.state.product_page = 1
        self.run_async(self.reload_catalog(page=1))

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
