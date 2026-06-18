from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, Callable

import flet as ft

from app.frontend.views.theme import (
    IschuuColors,
    app_border,
    input_style,
    outline_button_style,
    primary_button_style,
)

if TYPE_CHECKING:
    from app.frontend.controllers.app_controller import AppController


HELP_CATEGORIES = {
    "inicio": ("Inicio", ft.Icons.HOME_OUTLINED),
    "preguntas": ("Preguntas frecuentes", ft.Icons.QUIZ_OUTLINED),
    "compras": ("Compras y puntos", ft.Icons.SHOPPING_BAG_OUTLINED),
    "pagos": ("Pagos con Webpay", ft.Icons.CREDIT_CARD_OUTLINED),
    "pedidos": ("Pedidos y entrega", ft.Icons.LOCAL_SHIPPING_OUTLINED),
    "cambios": ("Cambios y garantías", ft.Icons.SWAP_HORIZ),
    "cuenta": ("Mi cuenta", ft.Icons.PERSON_OUTLINE),
    "contacto": ("Contacto", ft.Icons.SUPPORT_AGENT),
}


FAQS = [
    {
        "category": "compras",
        "question": "¿Cómo realizo una compra?",
        "answer": (
            "Explora el catálogo, agrega los productos al carrito y completa tu "
            "dirección de despacho. Al presionar “Pagar con Webpay” saldrás al "
            "flujo seguro de pago. Tu pedido se confirma cuando Webpay autoriza "
            "la transacción."
        ),
    },
    {
        "category": "compras",
        "question": "¿Cómo encuentro un producto?",
        "answer": (
            "En Tienda puedes buscar por nombre, serie o categoría y usar el "
            "selector de categorías para acotar el catálogo."
        ),
    },
    {
        "category": "compras",
        "question": "¿Cómo funcionan los puntos Ischuu?",
        "answer": (
            "Los puntos se asocian a tu cuenta después de una compra autorizada. "
            "Cuando tengas puntos disponibles, activa “Usar puntos disponibles” "
            "en el carrito; allí verás el descuento calculado antes de pagar."
        ),
    },
    {
        "category": "compras",
        "question": "¿Qué significa que un producto esté sin stock?",
        "answer": (
            "Significa que no quedan unidades disponibles para comprar. El stock "
            "se actualiza después de cada pago autorizado."
        ),
    },
    {
        "category": "pagos",
        "question": "¿Qué medios de pago acepta Ischuu?",
        "answer": (
            "Los pagos de la app se procesan mediante Webpay Plus. Los medios "
            "habilitados se muestran directamente en la pantalla de Webpay."
        ),
    },
    {
        "category": "pagos",
        "question": "¿Por qué mi pago fue rechazado?",
        "answer": (
            "Puede deberse a datos incorrectos, saldo insuficiente, cancelación "
            "del flujo o rechazo del emisor. Regresa al carrito, verifica los "
            "datos e intenta nuevamente."
        ),
    },
    {
        "category": "pagos",
        "question": "Pagué, pero todavía no veo mi pedido",
        "answer": (
            "Espera unos segundos mientras Ischuu confirma la respuesta de "
            "Webpay. Si el pago fue autorizado y el pedido no aparece en Pedidos, "
            "contáctanos con el correo de tu cuenta y el comprobante."
        ),
    },
    {
        "category": "pedidos",
        "question": "¿Dónde reviso el estado de mi pedido?",
        "answer": (
            "Abre la sección Pedidos en la barra inferior. Allí verás el estado, "
            "los productos, la dirección de entrega, el total y los puntos "
            "obtenidos en cada compra."
        ),
    },
    {
        "category": "pedidos",
        "question": "¿Cuáles son las etapas de un pedido?",
        "answer": (
            "El seguimiento avanza por Pagado, Preparando, En despacho y "
            "Entregado. Un pedido también puede aparecer como Cancelado."
        ),
    },
    {
        "category": "pedidos",
        "question": "¿Puedo cambiar la dirección después de pagar?",
        "answer": (
            "La dirección queda registrada al crear el pedido. Contáctanos cuanto "
            "antes con tu número de pedido; podremos revisarlo solo si aún no ha "
            "sido despachado."
        ),
    },
    {
        "category": "pedidos",
        "question": "¿Cómo sé quién recibirá la compra?",
        "answer": (
            "En el detalle del pedido se muestran el destinatario, teléfono y "
            "dirección que confirmaste al pagar."
        ),
    },
    {
        "category": "cambios",
        "question": "¿Cómo solicito un cambio o devolución?",
        "answer": (
            "Escríbenos indicando el número de pedido, producto y motivo. Conserva "
            "el producto, sus accesorios y el empaque original mientras revisamos "
            "tu caso."
        ),
    },
    {
        "category": "cambios",
        "question": "¿Puedo devolver una Blind Box abierta?",
        "answer": (
            "Por ser un producto sorpresa y coleccionable, una Blind Box abierta "
            "puede no admitir devolución por preferencia. Una falla o un producto "
            "incorrecto se evalúan por separado."
        ),
    },
    {
        "category": "cambios",
        "question": "¿Qué hago si mi producto llegó dañado?",
        "answer": (
            "Toma fotografías claras del producto, empaque y etiqueta de despacho. "
            "Luego contáctanos con tu número de pedido para revisar la solución."
        ),
    },
    {
        "category": "cuenta",
        "question": "¿Necesito una cuenta para comprar?",
        "answer": (
            "Sí. Tu cuenta permite asociar el pago, guardar la dirección, acumular "
            "puntos y consultar el seguimiento de tus pedidos."
        ),
    },
    {
        "category": "cuenta",
        "question": "¿Cómo modifico mi dirección de despacho?",
        "answer": (
            "En el carrito presiona “Modificar dirección”, actualiza los datos y "
            "guárdalos antes de comenzar el pago."
        ),
    },
    {
        "category": "cuenta",
        "question": "¿Dónde veo mis puntos?",
        "answer": (
            "Tu saldo aparece en el encabezado y en Perfil. El detalle de puntos "
            "ganados también está disponible dentro de cada pedido."
        ),
    },
]


CATEGORY_DESCRIPTIONS = {
    "preguntas": "Todas las respuestas rápidas sobre el uso de Ischuu.",
    "compras": "Catálogo, carrito, stock y puntos de tu cuenta.",
    "pagos": "Confirmaciones, rechazos y flujo de pago con Webpay.",
    "pedidos": "Seguimiento, destinatario y entrega de tus compras.",
    "cambios": "Orientación para cambios, devoluciones y productos con problemas.",
    "cuenta": "Acceso, dirección de despacho y saldo de puntos.",
    "contacto": "Canales directos para hablar con el equipo de Ischuu.",
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _filtered_faqs(controller: "AppController") -> list[tuple[int, dict]]:
    query = _normalize(str(controller.help_search_query or "").strip())
    category = controller.help_category
    matches: list[tuple[int, dict]] = []

    for index, faq in enumerate(FAQS):
        category_match = category in {"inicio", "preguntas"} or faq["category"] == category
        category_title = HELP_CATEGORIES[faq["category"]][0]
        haystack = _normalize(f"{faq['question']} {faq['answer']} {category_title}")

        if category_match and (not query or query in haystack):
            matches.append((index, faq))

    return matches


def _section_title(title: str, subtitle: str = "") -> ft.Control:
    controls: list[ft.Control] = [
        ft.Text(title, size=21, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT)
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=IschuuColors.TEXT_MUTED))
    return ft.Column(spacing=4, controls=controls)


def _category_chip(controller: "AppController", key: str) -> ft.Control:
    label, icon = HELP_CATEGORIES[key]
    selected = controller.help_category == key
    content_color = IschuuColors.ON_PRIMARY if selected else IschuuColors.TEXT

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=13, vertical=10),
        border_radius=999,
        bgcolor=IschuuColors.PRIMARY_STRONG if selected else IschuuColors.SURFACE_ALT,
        border=app_border(
            IschuuColors.PRIMARY_STRONG if selected else IschuuColors.BORDER_SOFT
        ),
        on_click=lambda _e, category=key: controller.select_help_category(category),
        content=ft.Row(
            tight=True,
            spacing=7,
            controls=[
                ft.Icon(icon, size=17, color=content_color),
                ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=content_color),
            ],
        ),
    )


def _faq_item(controller: "AppController", index: int, faq: dict) -> ft.Control:
    is_open = controller.help_open_question == index

    body: list[ft.Control] = [
        ft.ListTile(
            leading=ft.Icon(
                HELP_CATEGORIES[faq["category"]][1],
                color=IschuuColors.PRIMARY,
                size=21,
            ),
            title=ft.Text(
                faq["question"],
                size=14,
                weight=ft.FontWeight.W_600,
                color=IschuuColors.TEXT,
            ),
            subtitle=ft.Text(
                HELP_CATEGORIES[faq["category"]][0],
                size=11,
                color=IschuuColors.TEXT_SOFT,
            ),
            trailing=ft.Icon(
                ft.Icons.EXPAND_LESS if is_open else ft.Icons.EXPAND_MORE,
                color=IschuuColors.PRIMARY,
            ),
            on_click=lambda _e, question=index: controller.toggle_help_question(question),
        )
    ]

    if is_open:
        body.extend(
            [
                ft.Divider(height=1, color=IschuuColors.BORDER),
                ft.Container(
                    padding=ft.Padding(left=18, top=14, right=18, bottom=18),
                    content=ft.Text(faq["answer"], size=13, color=IschuuColors.TEXT_MUTED),
                ),
            ]
        )

    return ft.Container(
        bgcolor=IschuuColors.SURFACE,
        border=app_border(),
        border_radius=16,
        content=ft.Column(spacing=0, controls=body),
    )


def _faq_list(controller: "AppController", featured: list[int] | None = None) -> ft.Control:
    matches = _filtered_faqs(controller)
    if featured is not None and not controller.help_search_query:
        matches = [(index, FAQS[index]) for index in featured]

    if not matches:
        return ft.Container(
            padding=28,
            alignment=ft.Alignment.CENTER,
            bgcolor=IschuuColors.SURFACE,
            border=app_border(),
            border_radius=18,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.SEARCH_OFF_OUTLINED, size=42, color=IschuuColors.TEXT_SOFT),
                    ft.Text("No encontramos una respuesta", weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                    ft.Text(
                        "Prueba otra palabra o revisa una categoría.",
                        text_align=ft.TextAlign.CENTER,
                        color=IschuuColors.TEXT_MUTED,
                    ),
                    ft.TextButton(
                        content="Limpiar búsqueda",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda _e: controller.clear_help_search(),
                    ),
                ],
            ),
        )

    return ft.Column(
        spacing=10,
        controls=[_faq_item(controller, index, faq) for index, faq in matches],
    )


def _quick_card(
    icon: str,
    title: str,
    description: str,
    on_click: Callable,
) -> ft.Control:
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 3},
        padding=16,
        bgcolor=IschuuColors.SURFACE,
        border=app_border(),
        border_radius=18,
        on_click=on_click,
        content=ft.Column(
            spacing=9,
            controls=[
                ft.Container(
                    width=42,
                    height=42,
                    alignment=ft.Alignment.CENTER,
                    border_radius=14,
                    bgcolor=IschuuColors.SURFACE_ALT,
                    content=ft.Icon(icon, color=IschuuColors.PRIMARY, size=24),
                ),
                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                ft.Text(description, size=12, color=IschuuColors.TEXT_MUTED),
                ft.Row(
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Text("Ver ayuda", size=12, color=IschuuColors.PRIMARY),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=15, color=IschuuColors.PRIMARY),
                    ],
                ),
            ],
        ),
    )


def _orders_card(controller: "AppController") -> ft.Control:
    bullets = [
        "Consulta el avance de tus compras",
        "Revisa dirección, destinatario y total",
        "Comprueba el pago y los puntos ganados",
    ]

    return ft.Container(
        padding=20,
        border_radius=20,
        gradient=ft.LinearGradient(colors=IschuuColors.FEATURE_GRADIENT),
        border=app_border(IschuuColors.PRIMARY_DARK),
        content=ft.ResponsiveRow(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    col={"xs": 12, "md": 8},
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=IschuuColors.PRIMARY, size=28),
                                    ft.Text("Revisa y gestiona tus pedidos", size=18, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                                ],
                            ),
                            *[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=IschuuColors.SUCCESS),
                                        ft.Text(label, size=12, color=IschuuColors.TEXT_MUTED),
                                    ],
                                )
                                for label in bullets
                            ],
                        ],
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "md": 4},
                    alignment=ft.Alignment.CENTER_RIGHT,
                    content=ft.FilledButton(
                        content="Ir a mis pedidos",
                        icon=ft.Icons.LOCAL_SHIPPING_OUTLINED,
                        style=primary_button_style(),
                        on_click=lambda _e: controller.open_orders_from_help(),
                    ),
                ),
            ],
        ),
    )


def _contact_section(controller: "AppController") -> ft.Control:
    return ft.Container(
        padding=20,
        bgcolor=IschuuColors.SURFACE,
        border=app_border(),
        border_radius=20,
        content=ft.ResponsiveRow(
            run_spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    col={"xs": 12, "md": 7},
                    content=ft.Row(
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                alignment=ft.Alignment.CENTER,
                                border_radius=16,
                                bgcolor=IschuuColors.SURFACE_ALT,
                                content=ft.Icon(ft.Icons.HEADSET_MIC_OUTLINED, color=IschuuColors.PRIMARY, size=27),
                            ),
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Text("¿Aún necesitas ayuda?", size=18, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                                    ft.Text(
                                        "Escríbenos con tu número de pedido si tu consulta corresponde a una compra.",
                                        size=12,
                                        color=IschuuColors.TEXT_MUTED,
                                    ),
                                    ft.Text("+56 9 6193 4594 · soporte@ischuu.cl", size=12, color=IschuuColors.TEXT_SOFT),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "md": 5},
                    content=ft.Row(
                        wrap=True,
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.OutlinedButton(
                                content="WhatsApp",
                                icon=ft.Icons.CHAT_OUTLINED,
                                style=outline_button_style(),
                                on_click=lambda _e: controller.open_help_whatsapp(),
                            ),
                            ft.OutlinedButton(
                                content="Correo",
                                icon=ft.Icons.EMAIL_OUTLINED,
                                style=outline_button_style(),
                                on_click=lambda _e: controller.open_help_email(),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


def _build_home(controller: "AppController") -> ft.Control:
    return ft.Column(
        spacing=18,
        controls=[
            _section_title("Resuelve lo más común", "Accesos rápidos según lo que necesitas hacer."),
            ft.ResponsiveRow(
                spacing=12,
                run_spacing=12,
                controls=[
                    _quick_card(ft.Icons.SHOPPING_CART_OUTLINED, "Comprar", "Carrito, stock y puntos.", lambda _e: controller.select_help_category("compras")),
                    _quick_card(ft.Icons.CREDIT_CARD_OUTLINED, "Pagar", "Webpay y confirmaciones.", lambda _e: controller.select_help_category("pagos")),
                    _quick_card(ft.Icons.LOCAL_SHIPPING_OUTLINED, "Seguir pedido", "Estado y entrega.", lambda _e: controller.select_help_category("pedidos")),
                    _quick_card(ft.Icons.SWAP_HORIZ, "Resolver problema", "Cambios y garantías.", lambda _e: controller.select_help_category("cambios")),
                ],
            ),
            _orders_card(controller),
            _section_title("Preguntas más consultadas"),
            _faq_list(controller, featured=[0, 2, 5, 7]),
            _contact_section(controller),
        ],
    )


def _build_category(controller: "AppController") -> ft.Control:
    key = controller.help_category
    if key == "contacto":
        return ft.Column(
            spacing=18,
            controls=[
                _section_title("Hablemos", CATEGORY_DESCRIPTIONS["contacto"]),
                _contact_section(controller),
            ],
        )

    title = HELP_CATEGORIES.get(key, HELP_CATEGORIES["preguntas"])[0]
    return ft.Column(
        spacing=18,
        controls=[
            _section_title(title, CATEGORY_DESCRIPTIONS.get(key, "Encuentra la respuesta que necesitas.")),
            _faq_list(controller),
            _contact_section(controller),
        ],
    )


def _build_search_results(controller: "AppController") -> ft.Control:
    return ft.Column(
        spacing=18,
        controls=[
            _section_title(
                f'Resultados para “{controller.help_search_query}”',
                "Selecciona una pregunta para ver la respuesta.",
            ),
            _faq_list(controller),
            _contact_section(controller),
        ],
    )


def build_help_view(controller: "AppController") -> ft.Control:
    search_field = ft.TextField(
        value=controller.help_search_query,
        hint_text="Busca por pedido, Webpay, puntos, devolución...",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=controller.on_help_search,
        **input_style(),
    )

    search_row = ft.Row(
        spacing=10,
        controls=[
            ft.Container(expand=True, content=search_field),
            ft.FilledButton(
                content="Buscar",
                icon=ft.Icons.ARROW_FORWARD,
                style=primary_button_style(),
                on_click=lambda _e: controller.set_help_search(search_field.value),
            ),
        ],
    )

    content = (
        _build_search_results(controller)
        if controller.help_search_query
        else _build_home(controller)
        if controller.help_category == "inicio"
        else _build_category(controller)
    )

    return ft.Column(
        spacing=18,
        controls=[
            ft.Container(
                padding=20,
                border_radius=22,
                gradient=ft.LinearGradient(colors=IschuuColors.HEADER_GRADIENT),
                border=app_border(IschuuColors.PRIMARY_DARK),
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Icon(ft.Icons.SUPPORT_AGENT, size=32, color=IschuuColors.PRIMARY),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text("Centro de ayuda", size=26, weight=ft.FontWeight.BOLD, color=IschuuColors.TEXT),
                                        ft.Text("Respuestas claras para comprar y usar Ischuu.", size=13, color=IschuuColors.TEXT_MUTED),
                                    ],
                                ),
                            ],
                        ),
                        search_row,
                    ],
                ),
            ),
            ft.Row(
                scroll=ft.ScrollMode.AUTO,
                spacing=9,
                controls=[_category_chip(controller, key) for key in HELP_CATEGORIES],
            ),
            content,
        ],
    )
