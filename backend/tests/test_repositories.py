"""
Tests for repositories — data access layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import Select


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_by_telegram_id_found(self, mock_session):
        """Repository returns user when telegram_id exists."""
        from src.repositories.user_repo import UserRepository
        from src.db.models.user import User

        user = User(id=123, telegram_id=123, username="testuser")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_session)
        result = await repo.get_by_telegram_id(123)

        assert result is not None
        assert result.telegram_id == 123
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_telegram_id_not_found(self, mock_session):
        """Repository returns None when telegram_id doesn't exist."""
        from src.repositories.user_repo import UserRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_session)
        result = await repo.get_by_telegram_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_user(self, mock_session):
        """Repository creates a new user."""
        from src.repositories.user_repo import UserRepository

        repo = UserRepository(mock_session)
        user = await repo.create(
            telegram_id=456,
            username="newuser",
            first_name="New",
            last_name="User",
            language_code="ru",
        )

        assert user.telegram_id == 456
        assert user.username == "newuser"
        assert user.id == 456  # id = telegram_id
        mock_session.add.assert_called_once_with(user)
