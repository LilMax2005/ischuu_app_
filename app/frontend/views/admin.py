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
    "Compra realizada",
    "Artículo empaquetado",
    "Artículo enviado",
    "Artículo entregado",
]


def build_admin_view(controller: "AppController") -> ft.Control:
    admin_tab = getattr(controller, "admin_tab", "stock")

    def change_tab(tab_name: str) -> None:
        controller.admin_tab = tab_name
        controller.render()

    if admin_tab == "stock":
        content = build_admin_stock(controller)
    elif admin_tab == "orders":
        content = build_admin_orders(controller)
    else:
        content = build_admin_users(controller)

    return ft.Column(
        spacing=14,
        controls=[
            section_title("Panel de administrador", 22),
            muted_text("Gestiona stock, usuarios y seguimiento de pedidos."),

            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    ft.FilledButton(
                        content="Stock",
                        icon=ft.Icons.INVENTORY_2_OUTLINED,
                        on_click=lambda e: change_tab("stock"),
                        style=primary_button_style() if admin_tab == "stock" else outline_button_style(),
                    ),
                    ft.FilledButton(
                        content="Pedidos",
                        icon=ft.Icons.LOCAL_SHIPPING_OUTLINED,
                        on_click=lambda e: change_tab("orders"),
                        style=primary_button_style() if admin_tab == "orders" else outline_button_style(),
                    ),
                    ft.FilledButton(
                        content="Usuarios",
                        icon=ft.Icons.GROUP_OUTLINED,
                        on_click=lambda e: change_tab("users"),
                        style=primary_button_style() if admin_tab == "users" else outline_button_style(),
                    ),
                ],
            ),

            content,
        ],
    )


def build_admin_stock(controller: "AppController") -> ft.Control:
    products = getattr(controller, "admin_products", []) or []

    if not products:
        return card(
            ft.Column(
                spacing=10,
                controls=[
                    muted_text("No hay productos cargados."),
                    ft.OutlinedButton(
                        content="Recargar productos",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: controller.run_async(controller.load_admin_data()),
                        style=outline_button_style(),
                    ),
                ],
            )
        )

    return ft.Column(
        spacing=12,
        controls=[build_product_admin_card(controller, product) for product in products],
    )


def build_product_admin_card(controller: "AppController", product: dict) -> ft.Control:
    quantity_field = ft.TextField(
        label="Cantidad",
        value="1",
        width=130,
        prefix_icon=ft.Icons.ADD,
        **input_style(),
    )

    stock_field = ft.TextField(
        label="Nuevo stock",
        value=str(product.get("stock", 0)),
        width=150,
        prefix_icon=ft.Icons.INVENTORY_2_OUTLINED,
        **input_style(),
    )

    def add_stock(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.admin_update_stock(
                product["id"],
                operation="add",
                quantity=int(quantity_field.value or 0),
            )
        )

    def set_stock(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.admin_update_stock(
                product["id"],
                operation="set",
                stock=int(stock_field.value or 0),
            )
        )

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            controls=[
                                ft.Text(
                                    product.get("name", ""),
                                    color=IschuuColors.TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"{product.get('category', '')} · {currency(int(product.get('price', 0)))}",
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
                            content="Reponer stock",
                            icon=ft.Icons.INVENTORY_OUTLINED,
                            on_click=set_stock,
                            style=outline_button_style(),
                        ),
                    ],
                ),
            ],
        )
    )


def build_admin_orders(controller: "AppController") -> ft.Control:
    orders = getattr(controller, "admin_orders", []) or []

    if not orders:
        return card(muted_text("Aún no hay pedidos registrados."))

    return ft.Column(
        spacing=12,
        controls=[build_order_admin_card(controller, order) for order in orders],
    )


def build_order_admin_card(controller: "AppController", order: dict) -> ft.Control:
    status_dropdown = ft.Dropdown(
        label="Estado del pedido",
        value=order.get("status", "Compra realizada"),
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
            controller.admin_update_order_status(
                order["id"],
                status_dropdown.value or "Compra realizada",
            )
        )

    items = order.get("items", []) or []
    items_text = ", ".join(
        [
            f"{item.get('name', 'Producto')} x{item.get('quantity', 1)}"
            for item in items
        ]
    )

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            controls=[
                                ft.Text(
                                    f"Pedido #{order.get('id', '')}",
                                    color=IschuuColors.TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    items_text or "Sin detalle de productos",
                                    color=IschuuColors.TEXT_MUTED,
                                    size=13,
                                ),
                            ],
                        ),
                        status_pill(order.get("status", "Compra realizada"), "success"),
                    ],
                ),
                build_summary_row(
                    "Total",
                    currency(int(order.get("total", 0))),
                    highlight=True,
                ),
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
            ],
        )
    )


def build_admin_users(controller: "AppController") -> ft.Control:
    users = getattr(controller, "admin_users", []) or []

    if not users:
        return card(muted_text("No hay usuarios cargados."))

    return ft.Column(
        spacing=12,
        controls=[build_user_admin_card(controller, user) for user in users],
    )


def build_user_admin_card(controller: "AppController", user: dict) -> ft.Control:
    active_switch = ft.Switch(value=bool(user.get("is_active", True)), label="Activo")
    admin_switch = ft.Switch(value=bool(user.get("is_admin", False)), label="Admin")

    points_field = ft.TextField(
        label="Puntos",
        value=str(user.get("points", 0)),
        width=130,
        prefix_icon=ft.Icons.STARS_OUTLINED,
        **input_style(),
    )

    def save_user(_: ft.ControlEvent) -> None:
        controller.run_async(
            controller.admin_update_user(
                user["id"],
                is_active=active_switch.value,
                is_admin=admin_switch.value,
                points=int(points_field.value or 0),
            )
        )

    return card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            controls=[
                                ft.Text(
                                    user.get("name", ""),
                                    color=IschuuColors.TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    user.get("email", ""),
                                    color=IschuuColors.TEXT_MUTED,
                                    size=13,
                                ),
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
        )
    )