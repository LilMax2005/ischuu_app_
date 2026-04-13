import flet as ft

from app.controllers.app_controller import AppController


def main(page: ft.Page) -> None:
    AppController(page)


if __name__ == "__main__":
    ft.run(main)
