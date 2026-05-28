from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ischuu"

    secret_key: str = "CAMBIAR_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    mongodb_url: str
    mongodb_database: str = "ischuu"

    api_base_url: str = "https://ischuu-app.onrender.com"

    tbk_env: str = "integration"
    tbk_commerce_code: str = ""
    tbk_api_key: str = ""

    membership_amount: int = 20000

    # SMTP / Correos
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()