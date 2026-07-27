"""
Tests for Deduplicator — exact and fuzzy event dedup.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestDeduplicator:
    @pytest.mark.asyncio
    async def test_filter_new_events(self):
        """Events not seen before should pass through."""
        from src.aggregator.deduplicator import Deduplicator

        mock_session = AsyncMock()
        # No existing source items found
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        dedup = Deduplicator(mock_session)
        await dedup.build_index("test-source", 1)

        raw_events = _make_raw_events(["Event 1", "Event 2"])
        new = await dedup.filter_new(raw_events)

        assert len(new) == 2

    @pytest.mark.asyncio
    async def test_filter_duplicate_by_guid(self):
        """Events with existing item_guid should be filtered out."""
        from src.aggregator.deduplicator import Deduplicator

        mock_session = AsyncMock()
        # Existing source items with matching guids — return as tuples (row[0])
        mock_result = MagicMock()
        mock_result.all.return_value = [("hash-event-1",), ("hash-event-3",)]
        mock_session.execute = AsyncMock(return_value=mock_result)

        dedup = Deduplicator(mock_session)
        await dedup.build_index("test-source", 1)

        raw_events = _make_raw_events(["Event 1", "Event 2", "Event 3"])
        new = await dedup.filter_new(raw_events)

        assert len(new) == 1
        assert new[0].title == "Event 2"

    @pytest.mark.asyncio
    async def test_all_duplicates(self):
        """When all events are duplicates, return empty list."""
        from src.aggregator.deduplicator import Deduplicator

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [("hash-event-1",)]
        mock_session.execute = AsyncMock(return_value=mock_result)

        dedup = Deduplicator(mock_session)
        await dedup.build_index("test-source", 1)

        raw_events = _make_raw_events(["Event 1"])
        new = await dedup.filter_new(raw_events)

        assert new == []

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Empty input returns empty result."""
        from src.aggregator.deduplicator import Deduplicator

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        dedup = Deduplicator(mock_session)
        await dedup.build_index("test-source", 1)

        new = await dedup.filter_new([])
        assert new == []


def _make_raw_events(titles: list[str]) -> list:
    """Create RawEvent objects with deterministic guids."""
    from src.aggregator.models import RawEvent

    events = []
    for i, title in enumerate(titles, 1):
        guid_slug = title.lower().replace(" ", "-")
        events.append(RawEvent(
            title=title,
            content_source_id=1,
            source_slug="test-source",
            source_item_guid=f"hash-{guid_slug}",
        ))
    return events
