from __future__ import annotations

import flet as ft

from app.frontend.controllers.app_controller import AppController
from app.frontend.config import api_base_url


API_BASE_URL = api_base_url()


def main(page: ft.Page) -> None:
    AppController(
        page,
        api_base_url=API_BASE_URL,
    )


if __name__ == "__main__":
    ft.run(main)
