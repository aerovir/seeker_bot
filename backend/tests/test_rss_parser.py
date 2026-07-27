"""
Tests for RSS parser — RSSParser.
"""

import pytest
from unittest.mock import patch

from src.common.exceptions import ParseError


class TestRSSParser:
    @pytest.mark.asyncio
    async def test_parse_rss_items(self):
        """RSSParser extracts items from RSS feed."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType

        source = ContentSource(
            id=1,
            name="Test RSS",
            slug="test-rss",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Выставка Айвазовского",
                    "link": "https://example.com/event1",
                    "summary": "В Третьяковской галерее открылась выставка",
                    "published_parsed": None,
                    "tags": [{"term": "Выставки"}],
                },
                {
                    "title": "Спектакль в Большом театре",
                    "link": "https://example.com/event2",
                    "summary": "Премьера балета в Москве",
                    "published_parsed": None,
                    "tags": [],
                },
            ],
            "feed": {"title": "Test Feed"},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert len(events) == 2
        assert events[0].title == "Выставка Айвазовского"
        assert events[0].source_slug == "test-rss"
        assert events[0].content_source_id == 1
        assert events[1].title == "Спектакль в Большом театре"

    @pytest.mark.asyncio
    async def test_parse_rss_with_dates(self):
        """RSSParser extracts dates from RSS feed."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType
        import time
        from datetime import datetime

        published_time = time.mktime(datetime(2026, 7, 15).timetuple())

        source = ContentSource(
            id=2,
            name="Test RSS",
            slug="test-rss",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Test Event",
                    "link": "https://example.com",
                    "summary": "Desc",
                    "published_parsed": time.struct_time(time.localtime(published_time)),
                    "tags": [],
                },
            ],
            "feed": {"title": "Test"},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert len(events) == 1
        assert events[0].start_date is not None

    @pytest.mark.asyncio
    async def test_parse_empty_feed(self):
        """RSSParser handles empty feed."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType

        source = ContentSource(
            id=1,
            name="Test",
            slug="test",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        mock_feed = {"entries": [], "feed": {}}

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert events == []

    @pytest.mark.asyncio
    async def test_parse_invalid_xml(self):
        """RSSParser raises ParseError on invalid data."""
        from src.aggregator.parsers.rss_parser import RSSParser

        parser = RSSParser()
        with patch("feedparser.parse", return_value={"bozo": True, "bozo_exception": Exception("Parse failed")}):
            with pytest.raises(ParseError):
                await parser.parse(b"invalid", None)
