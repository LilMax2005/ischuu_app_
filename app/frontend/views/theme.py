from __future__ import annotations

import flet as ft


DARK_PALETTE = {
    "BG": "#0B0F14",
    "SURFACE": "#151A21",
    "SURFACE_ALT": "#202733",
    "SURFACE_SOFT": "#2A3442",
    "PRIMARY": "#F3A7C8",
    "PRIMARY_STRONG": "#EC4899",
    "PRIMARY_DARK": "#BE185D",
    "SECONDARY": "#A78BFA",
    "CREAM": "#FFF7ED",
    "VANILLA": "#FDE68A",
    "SKY": "#93C5FD",
    "SAGE": "#A7C7A1",
    "SUCCESS": "#86EFAC",
    "WARNING": "#FBBF24",
    "DANGER": "#F87171",
    "TEXT": "#F8FAFC",
    "TEXT_MUTED": "#CBD5E1",
    "TEXT_SOFT": "#94A3B8",
    "ON_PRIMARY": "#FFFFFF",
    "BORDER": "#334155",
    "BORDER_SOFT": "#475569",
    "HEADER_GRADIENT": ["#111827", "#25172B", "#4C1D3F"],
    "FEATURE_GRADIENT": ["#151A21", "#2C1830", "#4C1D3F"],
}


LIGHT_PALETTE = {
    "BG": "#FFF9FC",
    "SURFACE": "#FFFFFF",
    "SURFACE_ALT": "#FFF0F6",
    "SURFACE_SOFT": "#F4ECFF",
    "PRIMARY": "#B94D7F",
    "PRIMARY_STRONG": "#CC4D88",
    "PRIMARY_DARK": "#A83C70",
    "SECONDARY": "#8066B5",
    "CREAM": "#54243E",
    "VANILLA": "#9B641D",
    "SKY": "#4E78A5",
    "SAGE": "#4F7A5C",
    "SUCCESS": "#39805A",
    "WARNING": "#A96C12",
    "DANGER": "#C43D63",
    "TEXT": "#3C3038",
    "TEXT_MUTED": "#6F606A",
    "TEXT_SOFT": "#91808B",
    "ON_PRIMARY": "#FFFFFF",
    "BORDER": "#E7CCD9",
    "BORDER_SOFT": "#D8B6C7",
    "HEADER_GRADIENT": ["#FFF8FB", "#FDE8F1", "#EDE4FA"],
    "FEATURE_GRADIENT": ["#FFFFFF", "#FFF0F6", "#F3EBFF"],
}


class IschuuColors:
    pass


def apply_palette(light_mode: bool) -> None:
    palette = LIGHT_PALETTE if light_mode else DARK_PALETTE
    for name, value in palette.items():
        setattr(IschuuColors, name, value)


apply_palette(False)


class IschuuSize:
    CARD_RADIUS = 22
    INPUT_RADIUS = 14
    BUTTON_RADIUS = 14
    CHIP_RADIUS = 999
    CARD_PADDING = 16


def app_border(color: str | None = None, width: int = 1) -> ft.Border:
    border_color = color or IschuuColors.BORDER
    return ft.Border(
        left=ft.BorderSide(width, border_color),
        top=ft.BorderSide(width, border_color),
        right=ft.BorderSide(width, border_color),
        bottom=ft.BorderSide(width, border_color),
    )


def build_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=IschuuColors.PRIMARY_STRONG,
            secondary=IschuuColors.SECONDARY,
            surface=IschuuColors.SURFACE,
            error=IschuuColors.DANGER,
        )
    )


def primary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=IschuuColors.PRIMARY_STRONG,
        color=IschuuColors.ON_PRIMARY,
        shape=ft.RoundedRectangleBorder(radius=IschuuSize.BUTTON_RADIUS),
    )


def secondary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=IschuuColors.SURFACE_SOFT,
        color=IschuuColors.TEXT,
        shape=ft.RoundedRectangleBorder(radius=IschuuSize.BUTTON_RADIUS),
    )


def outline_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        color=IschuuColors.PRIMARY,
        side=ft.BorderSide(1, IschuuColors.PRIMARY),
        shape=ft.RoundedRectangleBorder(radius=IschuuSize.BUTTON_RADIUS),
    )


def danger_outline_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        color=IschuuColors.DANGER,
        side=ft.BorderSide(1, IschuuColors.DANGER),
        shape=ft.RoundedRectangleBorder(radius=IschuuSize.BUTTON_RADIUS),
    )


def input_style() -> dict:
    return {
        "filled": True,
        "bgcolor": IschuuColors.SURFACE_ALT,
        "color": IschuuColors.TEXT,
        "border_radius": IschuuSize.INPUT_RADIUS,
        "border_color": IschuuColors.BORDER,
        "focused_border_color": IschuuColors.PRIMARY_STRONG,
        "hint_style": ft.TextStyle(color=IschuuColors.TEXT_SOFT),
        "label_style": ft.TextStyle(color=IschuuColors.TEXT_MUTED),
    }


def card(content: ft.Control, padding: int = IschuuSize.CARD_PADDING) -> ft.Container:
    return ft.Container(
        padding=padding,
        border_radius=IschuuSize.CARD_RADIUS,
        bgcolor=IschuuColors.SURFACE,
        border=app_border(),
        content=content,
    )


def soft_card(content: ft.Control, padding: int = 14) -> ft.Container:
    return ft.Container(
        padding=padding,
        border_radius=IschuuSize.CARD_RADIUS - 6,
        bgcolor=IschuuColors.SURFACE_ALT,
        border=app_border(IschuuColors.BORDER_SOFT),
        content=content,
    )


def pill(label: str, icon: str | None = None, color: str | None = None) -> ft.Container:
    chip_color = color or IschuuColors.PRIMARY
    controls: list[ft.Control] = []

    if icon:
        controls.append(ft.Icon(icon, size=14, color=chip_color))

    controls.append(
        ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.W_600,
            color=IschuuColors.TEXT,
        )
    )

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=7),
        border_radius=IschuuSize.CHIP_RADIUS,
        bgcolor=IschuuColors.SURFACE_ALT,
        border=app_border(chip_color),
        content=ft.Row(spacing=6, tight=True, controls=controls),
    )


def status_pill(label: str, status: str = "info") -> ft.Container:
    color_map = {
        "success": IschuuColors.SUCCESS,
        "warning": IschuuColors.WARNING,
        "danger": IschuuColors.DANGER,
        "info": IschuuColors.SKY,
        "pink": IschuuColors.PRIMARY,
    }
    color = color_map.get(status, IschuuColors.SKY)

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        bgcolor=IschuuColors.SURFACE_ALT,
        border=app_border(color),
        content=ft.Text(
            label,
            size=12,
            color=color,
            weight=ft.FontWeight.W_600,
        ),
    )


def muted_text(value: str, size: int = 14) -> ft.Text:
    return ft.Text(value, size=size, color=IschuuColors.TEXT_MUTED)


def soft_text(value: str, size: int = 13) -> ft.Text:
    return ft.Text(value, size=size, color=IschuuColors.TEXT_SOFT)


def section_title(value: str, size: int = 22) -> ft.Text:
    return ft.Text(
        value,
        size=size,
        weight=ft.FontWeight.BOLD,
        color=IschuuColors.TEXT,
    )


def image_box(src: str, height: int = 170, width: int | None = None, border_radius: int = 16) -> ft.Container:
    return ft.Container(
        width=width,
        height=height,
        border_radius=border_radius,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=IschuuColors.SURFACE_ALT,
        border=app_border(),
        content=ft.Image(
            src=src,
            width=width,
            height=height,
            fit=ft.BoxFit.COVER,
            border_radius=border_radius,
        ),
    )
