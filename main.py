from __future__ import annotations

import os
import threading
import time

import flet as ft
import uvicorn
from dotenv import load_dotenv

from app.backend.main import app as backend_app
from app.frontend.controllers.app_controller import AppController

load_dotenv()

def run_backend() -> None:
    uvicorn.run(backend_app, host="127.0.0.1", port=8000, reload=False, log_level="info")

def main(page: ft.Page) -> None:
    AppController(page, api_base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))

if __name__ == "__main__":
    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()
    time.sleep(1)
    ft.run(main)
