"""
Tests for configuration — Pydantic Settings.

Note: pydantic-settings parses complex types (list, dict) from env as JSON.
"""

import os
import importlib
from unittest.mock import patch


def _reload_settings():
    """Force reload of settings module to pick up new env vars."""
    import src.config
    importlib.reload(src.config)
    from src.config import settings
    return settings


class TestConfig:
    """Test that config loads correctly from environment."""

    def test_settings_defaults(self):
        """Default values should be set when env vars are missing."""
        with patch.dict(os.environ, {
            "BOT_TOKEN": "test:token",
        }, clear=True):
            settings = _reload_settings()
            assert settings.bot_token == "test:token"
            assert settings.database_url.startswith("postgresql+asyncpg://")
            assert settings.redis_url.startswith("redis://")
            assert settings.log_level == "INFO"

    def test_settings_custom_values(self):
        """Custom env vars should override defaults."""
        with patch.dict(os.environ, {
            "BOT_TOKEN": "custom:token",
            "DATABASE_URL": "postgresql+asyncpg://custom:pass@host:5432/db",
            "REDIS_URL": "redis://custom:6379/1",
            "LOG_LEVEL": "DEBUG",
        }, clear=True):
            settings = _reload_settings()
            assert settings.bot_token == "custom:token"
            assert settings.database_url == "postgresql+asyncpg://custom:pass@host:5432/db"
            assert settings.redis_url == "redis://custom:6379/1"
            assert settings.log_level == "DEBUG"

    def test_admin_ids_parsing(self):
        """Admin IDs should be parsed as JSON list from env (pydantic-settings format)."""
        with patch.dict(os.environ, {
            "BOT_TOKEN": "test:token",
            "ADMIN_IDS": "[123,456,789]",
        }, clear=True):
            settings = _reload_settings()
            assert settings.admin_ids == [123, 456, 789]

    def test_admin_ids_empty(self):
        """Empty ADMIN_IDS should return default empty list."""
        with patch.dict(os.environ, {
            "BOT_TOKEN": "test:token",
        }, clear=True):
            settings = _reload_settings()
            assert settings.admin_ids == []
