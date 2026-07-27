"""
Tests for EventService — create events from raw data.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.common.constants import EventStatus


class TestEventService:
    @pytest.mark.asyncio
    async def test_create_from_raw_minimal(self):
        """EventService creates a DB event from minimal EnrichedEvent."""
        from src.services.event_service import EventService
        from src.aggregator.models import EnrichedEvent
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        service = EventService(mock_session)
        enriched = EnrichedEvent(
            title="Тестовое событие",
            description="Описание события",
            content_source_id=1,
            source_slug="test",
            source_item_guid="hash-123",
        )

        event = await service.create_from_raw(enriched, source)

        assert event.title == "Тестовое событие"
        assert event.description == "Описание события"
        assert event.source_id == 1
        assert event.status == EventStatus.PUBLISHED
        assert event.external_id == "test:hash-123"

    @pytest.mark.asyncio
    async def test_create_from_raw_full(self):
        """EventService creates a fully enriched DB event."""
        from src.services.event_service import EventService
        from src.aggregator.models import EnrichedEvent
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType
        from src.db.models.category import Category
        from datetime import datetime, timezone

        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        # Mock Category query used in event type detection
        mock_cat_result = MagicMock()
        cat = Category(id=1, slug="exhibitions", name_ru="Выставки", name_en="Exhibitions")
        mock_cat_result.scalars.return_value.all.return_value = [cat]
        mock_session.execute = AsyncMock(return_value=mock_cat_result)

        service = EventService(mock_session)
        enriched = EnrichedEvent(
            title="Большая выставка",
            description="Описание",
            short_description="Кратко",
            content_source_id=1,
            source_slug="test",
            source_item_guid="hash-456",
            url="https://example.com",
            image_url="https://example.com/img.jpg",
            start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
            is_multiday=True,
            venue_name="Музей",
            venue_address="Улица",
            price_min=500.0,
            price_max=1000.0,
            ticket_url="https://tickets.com",
            ticket_provider="yandex_afisha",
            categories=[(1, 0.95, "keyword")],
            cities=[(1, 1.0, "gazetteer")],
        )

        event = await service.create_from_raw(enriched, source)

        assert event.external_id == "test:hash-456"
        assert event.event_type == "exhibition"
        assert event.venue_name == "Музей"
        assert event.price_min == 500.0
        assert event.ticket_provider == "yandex_afisha"
        assert event.is_multiday is True

    @pytest.mark.asyncio
    async def test_detect_event_type(self):
        """Event type is detected from categories."""
        from src.services.event_service import EventService

        service = EventService(AsyncMock())

        assert service._detect_event_type([(1, 0.9, "keyword")], {1: "exhibitions"}) == "exhibition"
        assert service._detect_event_type([(2, 0.9, "keyword")], {2: "theatre"}) == "theatre"
        assert service._detect_event_type([], {}) == "other"
