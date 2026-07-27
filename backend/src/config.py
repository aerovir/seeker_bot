"""
Seeker Bot — Pydantic Settings for all config.

All environment variables are loaded via Pydantic Settings.
Single source of truth for configuration across the entire app.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Telegram
    bot_token: str
    admin_ids: list[int] = []

    # Database
    database_url: str = "postgresql+asyncpg://seeker:seeker_dev_pass@postgres:5432/seeker_bot"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Logging
    log_level: str = "INFO"
    sentry_dsn: str | None = None

    # Ticket APIs (optional)
    yandex_afisha_api_key: str | None = None
    kassir_api_key: str | None = None

    # Telegram Mini App
    tma_url: str = "http://localhost:5173"
    tma_secret: str | None = None


settings = Settings()
