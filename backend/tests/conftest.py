"""
Pytest fixtures for Seeker Bot tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_telegram_user():
    """Create a mock Telegram user."""
    user = MagicMock()
    user.id = 123456789
    user.is_bot = False
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.language_code = "ru"
    return user
