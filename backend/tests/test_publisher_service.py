"""
Tests for PublisherService — channel publishing logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from src.common.constants import PostStatus


class TestPublisherService:
    @pytest.mark.asyncio
    async def test_get_candidates_returns_events(self):
        """get_candidates returns published events not yet queued."""
        from src.services.publisher_service import PublisherService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        event = MagicMock()
        event.id = 1
        event.title = "Test Event"
        mock_result.scalars.return_value.all.return_value = [event]
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = PublisherService(mock_session)
        candidates = await service.get_candidates()

        assert len(candidates) == 1
        assert candidates[0].id == 1

    @pytest.mark.asyncio
    async def test_get_candidates_empty(self):
        """get_candidates returns empty list when no candidates."""
        from src.services.publisher_service import PublisherService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = PublisherService(mock_session)
        candidates = await service.get_candidates()

        assert candidates == []

    def test_build_channel_message_with_all_fields(self):
        """build_channel_message formats event with all fields."""
        from src.services.publisher_service import PublisherService

        event = _create_mock_event(
            title="Выставка Айвазовского",
            description="Описание выставки в Третьяковской галерее",
            event_type="exhibition",
            venue_name="Третьяковская галерея",
            start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
            price_min=500.0,
            price_max=1000.0,
            ticket_url="https://tickets.com/event",
            url="https://example.com/event",
            cities=[MagicMock(city=MagicMock(name_ru="Москва"))],
            categories=[MagicMock(category=MagicMock(emoji="🎨", name_ru="Выставки"))],
        )

        service = PublisherService(AsyncMock())
        text, markup = service.build_channel_message(event)

        assert "Выставка Айвазовского" in text
        assert "Третьяковская галерея" in text
        assert "🎨" in text
        assert "500" in text
        assert markup is not None
        # Место жирным + хэштеги города и категории
        assert "<b>Третьяковская галерея</b>" in text
        assert "#москва" in text
        assert "#выставки" in text

    def test_to_hashtag(self):
        """_to_hashtag нормализует строку в кириллический хэштег."""
        from src.services.publisher_service import PublisherService

        assert PublisherService._to_hashtag("Москва") == "москва"
        assert PublisherService._to_hashtag("Нижний Новгород") == "нижний_новгород"
        assert PublisherService._to_hashtag("Концерты") == "концерты"
        assert PublisherService._to_hashtag("") == ""

    def test_build_channel_message_minimal(self):
        """build_channel_message handles minimal event data."""
        from src.services.publisher_service import PublisherService

        event = _create_mock_event(
            title="Концерт",
            event_type="concert",
        )

        service = PublisherService(AsyncMock())
        text, markup = service.build_channel_message(event)

        assert "Концерт" in text
        # No ticket_url or url = no inline keyboard
        assert markup is None

    @pytest.mark.asyncio
    async def test_schedule_post(self):
        """schedule_post adds event to post queue."""
        from src.services.publisher_service import PublisherService

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        event = _create_mock_event(title="Test", event_type="test")

        service = PublisherService(mock_session)
        post = await service.schedule_post(event, delay_minutes=60)

        assert post.event_id == event.id
        assert post.status == PostStatus.SCHEDULED
        assert post.scheduled_at is not None

        # Check scheduled_at is ~60 min in future
        diff = (post.scheduled_at - datetime.now(timezone.utc)).total_seconds()
        assert 3500 < diff < 3700  # around 3600 seconds

    @pytest.mark.asyncio
    async def test_schedule_post_uses_settings_channel(self):
        """schedule_post without explicit channel_id uses settings.publisher_channel_id."""
        from unittest.mock import patch
        from src.services.publisher_service import PublisherService

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        event = _create_mock_event(title="Test", event_type="test")

        with patch("src.services.publisher_service.settings") as mock_settings:
            mock_settings.publisher_channel_id = "@default_channel"
            service = PublisherService(mock_session)
            post = await service.schedule_post(event, delay_minutes=60)

        assert post.channel_id == "@default_channel"

    @pytest.mark.asyncio
    async def test_schedule_post_explicit_channel_overrides(self):
        """Explicit channel_id overrides settings default."""
        from unittest.mock import patch
        from src.services.publisher_service import PublisherService

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        event = _create_mock_event(title="Test", event_type="test")

        with patch("src.services.publisher_service.settings") as mock_settings:
            mock_settings.publisher_channel_id = "@default_channel"
            service = PublisherService(mock_session)
            post = await service.schedule_post(event, delay_minutes=60, channel_id="@explicit")

        assert post.channel_id == "@explicit"

    @pytest.mark.asyncio
    async def test_get_scheduled_posts(self):
        """get_scheduled_posts returns posts due for publishing."""
        from src.services.publisher_service import PublisherService
        from src.db.models.post_queue import PostQueue

        mock_session = AsyncMock()
        mock_result = MagicMock()
        post = PostQueue(
            event_id=1, channel_id="@test", status=PostStatus.SCHEDULED,
            scheduled_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        mock_result.scalars.return_value.all.return_value = [post]
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = PublisherService(mock_session)
        posts = await service.get_scheduled_posts()

        assert len(posts) == 1
        assert posts[0].event_id == 1


def _create_mock_event(**kwargs) -> MagicMock:
    """Create a mock Event-like object."""
    event = MagicMock()
    event.id = kwargs.get("id", 1)
    event.title = kwargs.get("title", "Test Event")
    event.description = kwargs.get("description")
    event.short_description = kwargs.get("short_description")
    event.event_type = kwargs.get("event_type", "other")
    event.venue_name = kwargs.get("venue_name")
    event.venue_address = kwargs.get("venue_address")
    event.start_date = kwargs.get("start_date")
    event.end_date = kwargs.get("end_date")
    event.price_min = kwargs.get("price_min")
    event.price_max = kwargs.get("price_max")
    event.currency = kwargs.get("currency", "RUB")
    event.ticket_url = kwargs.get("ticket_url")
    event.ticket_provider = kwargs.get("ticket_provider")
    event.image_url = kwargs.get("image_url")
    event.url = kwargs.get("url")
    event.is_multiday = kwargs.get("is_multiday", False)
    event.cities = kwargs.get("cities", [])
    event.categories = kwargs.get("categories", [])
    return event
