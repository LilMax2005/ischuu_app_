from __future__ import annotations

import flet as ft


class IschuuColors:
    BG = "#0B0F14"
    SURFACE = "#151A21"
    SURFACE_ALT = "#202733"
    SURFACE_SOFT = "#2A3442"

    PRIMARY = "#F3A7C8"
    PRIMARY_STRONG = "#EC4899"
    PRIMARY_DARK = "#BE185D"
    SECONDARY = "#8B5CF6"

    CREAM = "#FFF7ED"
    VANILLA = "#FDE68A"
    SKY = "#93C5FD"
    SAGE = "#A7C7A1"

    SUCCESS = "#86EFAC"
    WARNING = "#FBBF24"
    DANGER = "#F87171"

    TEXT = "#F8FAFC"
    TEXT_MUTED = "#CBD5E1"
    TEXT_SOFT = "#94A3B8"

    BORDER = "#334155"
    BORDER_SOFT = "#475569"


class IschuuSize:
    CARD_RADIUS = 22
    INPUT_RADIUS = 14
    BUTTON_RADIUS = 14
    CHIP_RADIUS = 999
    CARD_PADDING = 16


def app_border(color: str = IschuuColors.BORDER, width: int = 1) -> ft.Border:
    return ft.Border(
        left=ft.BorderSide(width, color),
        top=ft.BorderSide(width, color),
        right=ft.BorderSide(width, color),
        bottom=ft.BorderSide(width, color),
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
        color=IschuuColors.TEXT,
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
