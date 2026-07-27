"""
Tests for NotificationService — digests and push notifications.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from src.common.constants import NotificationFrequency, NotificationType


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_send_digest(self):
        """send_digest sends digest message to user."""
        from src.services.notification_service import NotificationService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))

        user = User(id=123, telegram_id=12345, notification_frequency=NotificationFrequency.DIGEST_DAILY)
        events = [
            MagicMock(id=1, title="Event 1", event_type="exhibition", venue_name="Venue"),
            MagicMock(id=2, title="Event 2", event_type="concert"),
        ]

        service = NotificationService(mock_session, mock_bot)
        result = await service.send_digest(user, events)

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_digest_empty(self):
        """send_digest skips when no events."""
        from src.services.notification_service import NotificationService
        from src.db.models.user import User

        mock_session = AsyncMock()
        mock_bot = AsyncMock()

        user = User(id=123, telegram_id=12345)

        service = NotificationService(mock_session, mock_bot)
        result = await service.send_digest(user, [])

        assert result is False
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_digest_events(self):
        """get_digest_events returns events since last digest."""
        from src.services.notification_service import NotificationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(id=1, title="New Event"),
        ]
        mock_bot = AsyncMock()

        from src.db.models.user import User
        user = User(id=123, telegram_id=12345, last_digest_at=None)

        mock_session.execute = AsyncMock(return_value=mock_result)

        service = NotificationService(mock_session, mock_bot)
        events = await service.get_digest_events(user, days=1)

        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_get_digest_events_with_last(self):
        """get_digest_events filters since last_digest_at."""
        from src.services.notification_service import NotificationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_bot = AsyncMock()

        from src.db.models.user import User
        user = User(id=123, telegram_id=12345, last_digest_at=datetime(2020, 1, 1, tzinfo=timezone.utc))

        mock_session.execute = AsyncMock(return_value=mock_result)

        service = NotificationService(mock_session, mock_bot)
        events = await service.get_digest_events(user, days=1)

        assert events == []

    @pytest.mark.asyncio
    async def test_log_notification(self):
        """log_notification creates notification log entry."""
        from src.services.notification_service import NotificationService

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_bot = AsyncMock()

        service = NotificationService(mock_session, mock_bot)
        log = await service.log_notification(
            user_id=123,
            notification_type=NotificationType.DIGEST,
            title="Daily digest",
            was_delivered=True,
        )

        assert log.user_id == 123
        assert log.notification_type == NotificationType.DIGEST
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_digest_message(self):
        """build_digest_message formats digest with event list."""
        from src.services.notification_service import NotificationService

        mock_bot = AsyncMock()
        service = NotificationService(AsyncMock(), mock_bot)

        events = [
            MagicMock(id=1, title="Концерт", event_type="concert"),
            MagicMock(id=1, title="Выставка", event_type="exhibition"),
        ]

        text = service.build_digest_message(events)
        assert "Концерт" in text
        assert "Выставка" in text
        assert "🎵" in text
        assert "🎨" in text

    @pytest.mark.asyncio
    async def test_build_digest_message_empty(self):
        """build_digest_message returns None for empty list."""
        from src.services.notification_service import NotificationService

        service = NotificationService(AsyncMock(), AsyncMock())
        result = service.build_digest_message([])
        assert result is None

    @pytest.mark.asyncio
    async def test_send_breaking_news(self):
        """send_breaking_news sends single event to user."""
        from src.services.notification_service import NotificationService

        mock_session = AsyncMock()
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=456))

        event = MagicMock(
            id=1, title="Срочная новость", event_type="festival",
            venue_name="Площадь", start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
            categories=[], cities=[], short_description=None, venue_address=None,
            price_min=None, price_max=None, currency="RUB", ticket_url=None,
            url="https://example.com", image_url=None, is_multiday=False,
        )

        service = NotificationService(mock_session, mock_bot)
        result = await service.send_breaking_news(12345, event)

        assert result is True
        mock_bot.send_message.assert_called_once()
