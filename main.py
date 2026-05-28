from __future__ import annotations

import flet as ft

from app.frontend.controllers.app_controller import AppController


API_BASE_URL = "https://ischuu-app.onrender.com"


def main(page: ft.Page) -> None:
    AppController(
        page,
        api_base_url=API_BASE_URL,
    )


if __name__ == "__main__":
    ft.run(main)