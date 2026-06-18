from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from app.frontend.utils.formatters import currency
from app.frontend.views.components import build_summary_row
from app.frontend.views.theme import (
    IschuuColors,
    card,
    input_style,
    muted_text,
    outline_button_style,
    primary_button_style,
    section_title,
    status_pill,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


ORDER_STATUSES = [
    "Pagado",
    "Preparando",
    "En despacho",
    "Entregado",
    "Cancelado",
]


def build_admin_view(controller: "AppController") -> ft.Control:
    admin_tab = getattr(controller, "admin_tab", "dashboard")

    def change_tab(tab_name: str) -> None:
        controller.admin_tab = tab_name
        controller.render()

    content_builder = {
        "dashboard": build_admin_dashboard,
        "products": build_admin_products,
        "orders": build_admin_orders,
        "users": build_admin_users,
        "social": build_admin_social,
        "export": build_admin_export,
    }.get(admin_tab, build_admin_dashboard)

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Panel de administrador", 22),
            muted_text("Gestiona estadísticas, productos, pedidos, usuarios, redes sociales y exportaciones."),
            build_admin_menu(admin_tab, change_tab),
            content_builder(controller),
        ],
    )


def build_admin_menu(current_tab: str, change_tab) -> ft.Control:
    buttons = [
        ("dashboard", "Estadísticas", ft.Icons.QUERY_STATS),
        ("products", "Productos", ft.Icons.INVENTORY_2_OUTLINED),
        ("orders", "Pedidos", ft.Icons.LOCAL_SHIPPING_OUTLINED),
        ("users", "Usuarios", ft.Icons.GROUP_OUTLINED),
        ("social", "Redes", ft.Icons.LINK),
        ("export", "Exportar", ft.Icons.FILE_DOWNLOAD_OUTLINED),
    ]

    return ft.Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
        controls=[
            ft.FilledButton(
                content=label,
                icon=icon,
                on_click=lambda e, tab=tab: change_tab(tab),
                style=primary_button_style() if current_tab == tab else outline_button_style(),
            )
            for tab, label, icon in buttons
        ],
    )


# ============================================================
# DASHBOARD / ESTADÍSTICAS
# ============================================================

def build_admin_dashboard(controller: "AppController") -> ft.Control:
    summary = getattr(controller, "admin_summary", {}) or {}

    cards = [
        ("Usuarios", summary.get("users", 0), ft.Icons.GROUP_OUTLINED, "info"),
        ("Productos", summary.get("products", 0), ft.Icons.INVENTORY_2_OUTLINED, "pink"),
        ("Pedidos totales", summary.get("orders", 0), ft.Icons.RECEIPT_LONG_OUTLINED, "info"),
        ("Pagos aprobados", summary.get("paid_orders", 0), ft.Icons.CHECK_CIRCLE_OUTLINE, "success"),
        ("Ventas", currency(int(summary.get("revenue", 0))), ft.Icons.PAYMENTS_OUTLINED, "success"),
        ("Stock bajo", summary.get("low_stock", 0), ft.Icons.WARNING_AMBER_OUTLINED, "warning"),
    ]

    status_counts = summary.get("status_counts", {}) or {}

    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[build_stat_card(label, value, icon, status) for label, value, icon, status in cards],
            ),
            card(
                ft.Column(
                    spacing=8,
                    controls=(
                        [section_title("Estado de pedidos", 18)]
                        + [build_summary_row(status, str(status_counts.get(status, 0))) for status in ORDER_STATUSES]
                        if status_counts
                        else [section_title("Estado de pedidos", 18), muted_text("Aún no hay información de pedidos.")]
                    ),
                ),
                padding=16,
            ),
        ],
    )


def build_stat_card(label: str, value, icon: str, status: str = "info") -> ft.Control:
    color_map = {
        "success": IschuuColors.SUCCESS,
        "warning": IschuuColors.WARNING,
        "danger": IschuuColors.DANGER,
        "info": IschuuColors.SKY,
        "pink": IschuuColors.PRIMARY,
    }
    icon_color = color_map.get(status, IschuuColors.PRIMARY)

    return ft.Container(
        width=165,
        padding=16,
        border_radius=18,
        bgcolor=IschuuColors.SURFACE,
        border=ft.Border(
            left=ft.BorderSide(1, IschuuColors.BORDER),
            top=ft.BorderSide(1, IschuuColors.BORDER),
            right=ft.BorderSide(1, IschuuColors.BORDER),
            bottom=ft.BorderSide(1, IschuuColors.BORDER),
        ),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Icon(icon, color=icon_color, size=28),
                ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                ft.Text(label, color=IschuuColors.TEXT_MUTED, size=12),
            ],
        ),
    )


# ============================================================
# PRODUCTOS / CRUD
# ============================================================

def build_admin_products(controller: "AppController") -> ft.Control:
    products = getattr(controller, "admin_products", []) or []
    product_controls = [build_product_admin_card(controller, product) for product in products]

    if not product_controls:
        product_controls = [card(muted_text("No hay productos cargados en administración."), padding=20)]

    return ft.Column(
        spacing=12,
        controls=[
            build_product_form(controller),
            ft.Divider(color=IschuuColors.BORDER),
            section_title("Productos existentes", 18),
            *product_controls,
        ],
    )


def build_product_form(controller: "AppController") -> ft.Control:
    name = ft.TextField(
        label="Nombre",
        **input_style(),
    )

    series = ft.TextField(
        label="Serie",
        **input_style(),
    )

    category = ft.TextField(
        label="Categoría",
        value="General",
        **input_style(),
    )

    rarity = ft.TextField(
        label="Rareza",
        value="Común",
        **input_style(),
    )

    price = ft.TextField(
        label="Precio",
        value="0",
        width=160,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        **input_style(),
    )

    stock = ft.TextField(
        label="Stock",
        value="0",
        width=160,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        **input_style(),
    )

    description = ft.TextField(
        label="Descripción",
        height=90,
        **input_style(),
    )

    image_url = ft.TextField(
        label="URL imagen",
        hint_text="Ej: https://...",
        **input_style(),
    )

    image_path = ft.TextField(
        label="Ruta local de imagen opcional",
        hint_text=r"Ej: C:\Users\diegm\Pictures\producto.png",
        **input_style(),
    )

    def save(_: ft.ControlEvent) -> None:
        try:
            payload = {
                "name": name.value or "",
                "series": series.value or "",
                "category": category.value or "General",
                "rarity": rarity.value or "Común",
                "price": int(price.value or 0),
                "stock": int(stock.value or 0),
                "description": description.value or "",
                "image_url": image_url.value or "",
                "is_original": True,
            }

            controller.run_async(
                controller.admin_create_product(
                    payload,
                    image_path.value or "",
                )
            )

            name.value = ""
            series.value = ""
            category.value = "General"
            rarity.value = "Común"
            price.value = "0"
            stock.value = "0"
            description.value = ""
            image_url.value = ""
            image_path.value = ""

            controller.page.update()

        except Exception as exc:
            controller.show_message(
                f"Datos inválidos para crear producto: {exc}",
                error=True,
            )

    return card(
        ft.Column(
            spacing=12,
            controls=[
                section_title("Crear producto", 18),
                muted_text(
                    "Completa los datos del producto. Puedes usar una URL de imagen o una ruta local escrita manualmente."
                ),

                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        name,
                        series,
                    ],
                ),

                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        category,
                        rarity,
                        price,
                        stock,
                    ],
                ),

                description,
                image_url,
                image_path,

                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.FilledButton(
                            content="Crear producto",
                            icon=ft.Icons.SAVE,
                            on_click=save,
                            style=primary_button_style(),
                        ),
                    ],
                ),
            ],
        ),
        padding=16,
    )

def build_product_admin_card(controller: "AppController", product: dict) -> ft.Control:
    product_id = product.get("id", "")
    quantity_field = ft.TextField(
        label="Cantidad",
        value="1",
        width=130,
        prefix_icon=ft.Icons.ADD,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        **input_style(),
    )
    stock_field = ft.TextField(
        label="Nuevo stock",
        value=str(product.get("stock", 0)),
        width=150,
        prefix_icon=ft.Icons.INVENTORY_2_OUTLINED,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        **input_style(),
    )

    def add_stock(_: ft.ControlEvent) -> None:
        try:
            controller.run_async(
                controller.admin_update_stock(product_id, operation="add", quantity=int(quantity_field.value or 0))
            )
        except Exception as exc:
            controller.show_message(f"Cantidad inválida: {exc}", error=True)

    def set_stock(_: ft.ControlEvent) -> None:
        try:
            controller.run_async(
                controller.admin_update_stock(product_id, operation="set", stock=int(stock_field.value or 0))
            )
        except Exception as exc:
            controller.show_message(f"Stock inválido: {exc}", error=True)

    def delete(_: ft.ControlEvent) -> None:
        controller.run_async(controller.admin_delete_product(product_id))

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(product.get("name", ""), color=IschuuColors.TEXT, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{product.get('category', '')} · {product.get('series', '')} · {currency(int(product.get('price', 0)))}",
                                    color=IschuuColors.TEXT_MUTED,
                                    size=13,
                                ),
                            ],
                        ),
                        status_pill(f"Stock: {product.get('stock', 0)}", "info"),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        quantity_field,
                        ft.FilledButton(
                            content="Añadir stock",
                            icon=ft.Icons.ADD_BOX_OUTLINED,
                            on_click=add_stock,
                            style=primary_button_style(),
                        ),
                        stock_field,
                        ft.OutlinedButton(
                            content="Fijar stock",
                            icon=ft.Icons.INVENTORY_OUTLINED,
                            on_click=set_stock,
                            style=outline_button_style(),
                        ),
                        ft.OutlinedButton(
                            content="Eliminar",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=delete,
                            style=outline_button_style(),
                        ),
                    ],
                ),
            ],
        ),
        padding=16,
    )


# ============================================================
# PEDIDOS
# ============================================================

def build_admin_orders(controller: "AppController") -> ft.Control:
    orders = getattr(controller, "admin_orders", []) or []

    if not orders:
        return card(muted_text("Aún no hay pedidos registrados."), padding=20)

    return ft.Column(spacing=12, controls=[build_order_admin_card(controller, order) for order in orders])


def build_order_admin_card(controller: "AppController", order: dict) -> ft.Control:
    status_dropdown = ft.Dropdown(
        label="Estado del pedido",
        value=order.get("status", "Pagado"),
        options=[ft.dropdown.Option(status) for status in ORDER_STATUSES],
        width=280,
        bgcolor=IschuuColors.SURFACE_ALT,
        color=IschuuColors.TEXT,
        border_color=IschuuColors.BORDER,
        focused_border_color=IschuuColors.PRIMARY_STRONG,
        border_radius=14,
    )

    def update_status(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.admin_update_order_status(order.get("id", ""), status_dropdown.value or "Pagado")
        )

    items = order.get("items", []) or []
    items_text = ", ".join([f"{item.get('name', 'Producto')} x{item.get('quantity', 1)}" for item in items])
    history = order.get("status_history", []) or []
    history_controls = []

    if history:
        for h in history:
            history_controls.append(
                ft.Container(
                    padding=10,
                    border_radius=12,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Text(
                                f"{h.get('from', '')} → {h.get('to', '')}",
                                color=IschuuColors.TEXT,
                                weight=ft.FontWeight.BOLD,
                                size=12,
                            ),
                            ft.Text(
                                f"{h.get('changed_at', '')} · {h.get('changed_by', '')}",
                                color=IschuuColors.TEXT_MUTED,
                                size=11,
                            ),
                        ],
                    ),
                )
            )
    else:
        history_controls.append(muted_text("Sin historial registrado.", 12))

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    f"Pedido #{order.get('id', '')}",
                                    color=IschuuColors.TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    order.get("user_email", order.get("user_id", "")),
                                    color=IschuuColors.TEXT_MUTED,
                                    size=12,
                                ),
                                ft.Text(
                                    items_text or "Sin detalle de productos",
                                    color=IschuuColors.TEXT_MUTED,
                                    size=13,
                                ),
                            ],
                        ),
                        status_pill(order.get("status", "Pagado"), "success"),
                    ],
                ),
                build_summary_row("Total", currency(int(order.get("total", 0))), highlight=True),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        status_dropdown,
                        ft.FilledButton(
                            content="Actualizar estado",
                            icon=ft.Icons.UPDATE,
                            on_click=update_status,
                            style=primary_button_style(),
                        ),
                    ],
                ),
                ft.Divider(color=IschuuColors.BORDER),
                ft.Text("Historial de cambios", color=IschuuColors.TEXT, weight=ft.FontWeight.BOLD),
                ft.Column(spacing=6, controls=history_controls),
            ],
        ),
        padding=16,
    )


# ============================================================
# USUARIOS
# ============================================================

def build_admin_users(controller: "AppController") -> ft.Control:
    users = getattr(controller, "admin_users", []) or []

    if not users:
        return card(muted_text("No hay usuarios cargados."), padding=20)

    return ft.Column(spacing=12, controls=[build_user_admin_card(controller, user) for user in users])


def build_user_admin_card(controller: "AppController", user: dict) -> ft.Control:
    active_switch = ft.Switch(value=bool(user.get("is_active", True)), label="Activo")
    admin_switch = ft.Switch(value=bool(user.get("is_admin", False)), label="Admin")
    points_field = ft.TextField(
        label="Puntos",
        value=str(user.get("points", 0)),
        width=130,
        prefix_icon=ft.Icons.STARS_OUTLINED,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        **input_style(),
    )

    def save_user(_: ft.ControlEvent) -> None:
        try:
            controller.run_async(
                controller.admin_update_user(
                    user.get("id", ""),
                    is_active=bool(active_switch.value),
                    is_admin=bool(admin_switch.value),
                    points=int(points_field.value or 0),
                )
            )
        except Exception as exc:
            controller.show_message(f"Puntos inválidos: {exc}", error=True)

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(user.get("name", ""), color=IschuuColors.TEXT, weight=ft.FontWeight.BOLD),
                                ft.Text(user.get("email", ""), color=IschuuColors.TEXT_MUTED, size=13),
                            ],
                        ),
                        status_pill(
                            "Admin" if user.get("is_admin") else "Cliente",
                            "pink" if user.get("is_admin") else "info",
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        active_switch,
                        admin_switch,
                        points_field,
                        ft.FilledButton(
                            content="Guardar usuario",
                            icon=ft.Icons.SAVE,
                            on_click=save_user,
                            style=primary_button_style(),
                        ),
                    ],
                ),
            ],
        ),
        padding=16,
    )


# ============================================================
# CONFIGURACIÓN REDES
# ============================================================

def build_admin_social(controller: "AppController") -> ft.Control:
    settings = getattr(controller, "admin_settings", {}) or {}

    instagram_url = ft.TextField(
        label="Instagram URL",
        value=settings.get("instagram_url", "https://www.instagram.com/ischuu._"),
        **input_style(),
    )
    tiktok_url = ft.TextField(
        label="TikTok URL",
        value=settings.get("tiktok_url", "https://www.tiktok.com/"),
        **input_style(),
    )
    instagram_enabled = ft.Switch(label="Instagram activo", value=bool(settings.get("instagram_enabled", False)))
    tiktok_enabled = ft.Switch(label="TikTok activo", value=bool(settings.get("tiktok_enabled", False)))

    def save(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.admin_update_settings(
                {
                    "instagram_url": instagram_url.value or "",
                    "tiktok_url": tiktok_url.value or "",
                    "instagram_enabled": bool(instagram_enabled.value),
                    "tiktok_enabled": bool(tiktok_enabled.value),
                }
            )
        )

    return card(
        ft.Column(
            spacing=12,
            controls=[
                section_title("Integración Instagram / TikTok", 18),
                muted_text("Guarda las URLs oficiales. Para APIs reales se requieren credenciales de Meta/TikTok Developer."),
                instagram_url,
                tiktok_url,
                instagram_enabled,
                tiktok_enabled,
                ft.FilledButton(
                    content="Guardar redes",
                    icon=ft.Icons.SAVE,
                    on_click=save,
                    style=primary_button_style(),
                ),
            ],
        ),
        padding=16,
    )


# ============================================================
# EXPORTACIÓN
# ============================================================

def build_admin_export(controller: "AppController") -> ft.Control:
    def export(_: ft.ControlEvent) -> None:
        controller.run_async(controller.admin_export_orders())

    return card(
        ft.Column(
            spacing=12,
            controls=[
                section_title("Exportar pedidos", 18),
                muted_text("Descarga todos los pedidos en formato Excel para control, respaldo o análisis."),
                ft.FilledButton(
                    content="Exportar pedidos a Excel",
                    icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                    on_click=export,
                    style=primary_button_style(),
                ),
            ],
        ),
        padding=16,
    )
