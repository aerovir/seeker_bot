"""
Tests for UserService — user preferences management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestUserService:
    @pytest.mark.asyncio
    async def test_get_or_create_user_exists(self):
        """get_or_create returns existing user."""
        from src.services.user_service import UserService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_result = MagicMock()
        existing_user = User(id=123, telegram_id=123, username="existing")
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = UserService(mock_session)
        user = await service.get_or_create(telegram_id=123)

        assert user == existing_user
        assert user.username == "existing"

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self):
        """get_or_create creates a new user if not found."""
        from src.services.user_service import UserService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        # First call returns None (not found)
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_find_result)

        service = UserService(mock_session)
        user = await service.get_or_create(
            telegram_id=999,
            username="newuser",
            first_name="New",
        )

        assert user.telegram_id == 999
        assert user.username == "newuser"
        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_set_city_preferences(self):
        """User city preferences can be updated."""
        from src.services.user_service import UserService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        user = User(id=123, telegram_id=123)
        # Add some existing prefs
        from src.db.models.user import UserCityPreference
        existing_pref = UserCityPreference(user_id=123, city_id=5)
        user.city_preferences = [existing_pref]

        service = UserService(mock_session)
        await service.set_city_preferences(user, [1, 2, 3])

        # Old pref should be removed
        assert len(user.city_preferences) == 3
        assert user.city_preferences[0].city_id == 1
        assert user.city_preferences[1].city_id == 2
        assert user.city_preferences[2].city_id == 3

    @pytest.mark.asyncio
    async def test_set_category_preferences(self):
        """User category preferences can be updated."""
        from src.services.user_service import UserService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        user = User(id=456, telegram_id=456)

        service = UserService(mock_session)
        await service.set_category_preferences(user, [1, 4, 7])

        assert len(user.category_preferences) == 3
        assert user.category_preferences[2].category_id == 7
