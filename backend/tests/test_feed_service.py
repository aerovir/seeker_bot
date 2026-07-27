"""
Tests for FeedService — personalized event feed generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestFeedService:
    @pytest.mark.asyncio
    async def test_get_personalized_feed_default(self):
        """Feed returns events when user has no preferences."""
        from src.services.feed_service import FeedService
        from src.db.models.user import User

        mock_session = AsyncMock()

        # Mock event query result
        mock_events_result = MagicMock()
        event = MagicMock()
        event.id = 1
        event.title = "Test Event"
        event.status = "published"
        mock_events_result.scalars.return_value.all.return_value = [event]
        mock_events_result.scalars.return_value.first.return_value = None

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_events_result])

        user = User(id=123, telegram_id=123)
        user.city_preferences = []
        user.category_preferences = []

        service = FeedService(mock_session)
        events, total = await service.get_personalized_feed(user)

        assert len(events) == 1
        assert total == 1
        assert events[0].title == "Test Event"

    @pytest.mark.asyncio
    async def test_get_personalized_feed_with_preferences(self):
        """Feed filters by user's city and category preferences."""
        from src.services.feed_service import FeedService
        from src.db.models.user import User, UserCityPreference, UserCategoryPreference
        from src.db.models.city import City
        from src.db.models.category import Category

        mock_session = AsyncMock()

        # Mock city/category preference checks
        mock_city_result = MagicMock()
        mock_city_result.scalar_one_or_none.return_value = None  # no event for these prefs
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_city_result])

        user = User(id=456, telegram_id=456)
        user.city_preferences = [
            UserCityPreference(
                user_id=456, city_id=1, is_active=True,
                city=City(id=1, slug="moscow", name_ru="Москва", name_en="Moscow"),
            )
        ]
        user.category_preferences = [
            UserCategoryPreference(
                user_id=456, category_id=1, is_active=True,
                category=Category(id=1, slug="exhibitions", name_ru="Выставки", name_en="Exhibitions"),
            )
        ]

        service = FeedService(mock_session)
        events, total = await service.get_personalized_feed(user)

        assert events == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_personalized_feed_pagination(self):
        """Feed respects pagination parameters."""
        from src.services.feed_service import FeedService
        from src.db.models.user import User

        mock_session = AsyncMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_events_result = MagicMock()
        events = [MagicMock(id=i, title=f"Event {i}", status="published") for i in range(1, 11)]
        mock_events_result.scalars.return_value.all.return_value = events

        mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_events_result])

        user = User(id=789, telegram_id=789)
        user.city_preferences = []
        user.category_preferences = []

        service = FeedService(mock_session)
        events, total = await service.get_personalized_feed(user, page=2, page_size=10)

        assert len(events) == 10
        assert total == 50
