from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Ischuu"
    secret_key: str = "CAMBIAR_SECRET"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "ischuu"
    api_base_url: str = "http://127.0.0.1:8000"
    tbk_env: str = "integration"
    tbk_commerce_code: str = "597055555532"
    tbk_api_key: str = "REEMPLAZAR_API_KEY_TRANSBANK"
    membership_amount: int = 20000
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
