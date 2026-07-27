"""
Tests for aggregator models — RawEvent, EnrichedEvent.
"""

from datetime import datetime
from src.aggregator.models import RawEvent, EnrichedEvent, SourceRef


class TestSourceRef:
    def test_source_ref_creation(self):
        ref = SourceRef(source_id=1, source_slug="test-source", url="https://example.com")
        assert ref.source_id == 1
        assert ref.source_slug == "test-source"
        assert ref.url == "https://example.com"


class TestRawEvent:
    def test_raw_event_minimal(self):
        event = RawEvent(
            title="Test Event",
            description="Test description",
            content_source_id=1,
            source_slug="test",
            source_item_guid="guid-123",
        )
        assert event.title == "Test Event"
        assert event.source_item_guid == "guid-123"
        assert event.categories == []
        assert event.cities == []

    def test_raw_event_full(self):
        event = RawEvent(
            title="Full Event",
            description="Full description",
            content_source_id=1,
            source_slug="test",
            source_item_guid="guid-456",
            url="https://example.com/event",
            image_url="https://example.com/img.jpg",
            start_date=datetime(2026, 8, 15),
            end_date=datetime(2026, 9, 15),
            venue_name="Test Venue",
            venue_address="Test Address",
            price_text="500-1000 руб",
            categories=[(1, 0.95, "keyword")],
            cities=[(1, 1.0, "gazetteer")],
        )
        assert event.venue_name == "Test Venue"
        assert len(event.categories) == 1
        assert event.categories[0][0] == 1
        assert event.price_text == "500-1000 руб"


class TestEnrichedEvent:
    def test_enriched_from_raw(self):
        raw = RawEvent(
            title="Test",
            description="Desc",
            content_source_id=1,
            source_slug="test",
            source_item_guid="guid-1",
        )
        enriched = EnrichedEvent.from_raw(raw)
        assert enriched.title == "Test"
        assert enriched.ticket_url is None
        assert enriched.ticket_provider is None

    def test_enriched_with_tickets(self):
        raw = RawEvent(
            title="Test",
            description="Desc",
            content_source_id=1,
            source_slug="test",
            source_item_guid="guid-2",
        )
        enriched = EnrichedEvent.from_raw(raw)
        enriched.ticket_url = "https://tickets.com/event"
        enriched.ticket_provider = "yandex_afisha"
        enriched.price_min = 500.0
        enriched.price_max = 1000.0
        assert enriched.ticket_url == "https://tickets.com/event"
        assert enriched.price_min == 500.0
