"""
Tests for API Pydantic schemas — request/response models.
"""

import pytest
from datetime import datetime, timezone


class TestEventOutSchema:
    def test_event_out_from_orm(self):
        """EventOut can be created from an Event ORM object."""
        from src.api.schemas import EventOut
        from src.db.models.event import Event
        from src.common.constants import EventStatus

        event = Event(
            id=1,
            title="Тестовое событие",
            description="Описание",
            short_description="Кратко",
            event_type="exhibition",
            venue_name="Музей",
            venue_address="Улица",
            price_min=500.0,
            price_max=1000.0,
            ticket_url="https://tickets.com",
            status=EventStatus.PUBLISHED,
            start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        )

        out = EventOut.model_validate(event)

        assert out.id == 1
        assert out.title == "Тестовое событие"
        assert out.event_type == "exhibition"
        assert out.venue_name == "Музей"
        assert out.price_min == 500.0

    def test_event_out_no_optional_fields(self):
        """EventOut handles missing optional fields."""
        from src.api.schemas import EventOut
        from src.db.models.event import Event
        from src.common.constants import EventStatus

        event = Event(
            id=2,
            title="Минимальное событие",
            event_type="concert",
            status=EventStatus.PUBLISHED,
        )

        out = EventOut.model_validate(event)

        assert out.id == 2
        assert out.title == "Минимальное событие"
        assert out.venue_name is None
        assert out.price_min is None
        assert out.description is None


class TestPreferencesSchemas:
    def test_preferences_update_valid(self):
        """PreferencesUpdate validates correct input."""
        from src.api.schemas import PreferencesUpdate

        data = PreferencesUpdate(city_ids=[1, 2, 3], category_ids=[1, 4, 7])
        assert data.city_ids == [1, 2, 3]
        assert data.category_ids == [1, 4, 7]

    def test_preferences_update_too_many_cities(self):
        """PreferencesUpdate rejects more than MAX_USER_CITIES."""
        from src.api.schemas import PreferencesUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PreferencesUpdate(city_ids=list(range(1, 10)), category_ids=[1])

    def test_preferences_update_too_many_categories(self):
        """PreferencesUpdate rejects more than MAX_USER_CATEGORIES."""
        from src.api.schemas import PreferencesUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PreferencesUpdate(city_ids=[1], category_ids=list(range(1, 20)))


class TestFeedResponseSchema:
    def test_feed_response(self):
        """FeedResponse contains items, total, and page info."""
        from src.api.schemas import FeedResponse, EventOut

        response = FeedResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )

        assert response.page == 1
        assert response.total == 0
        assert response.total_pages == 0
