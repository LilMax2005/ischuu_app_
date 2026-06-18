from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE_URL = "https://ischuu-app.onrender.com"


def api_base_url() -> str:
    return os.getenv(
        "FRONTEND_API_BASE_URL",
        os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL),
    ).rstrip("/")
