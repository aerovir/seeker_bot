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

    @pytest.mark.asyncio
    async def test_parse_windows_1251_reencode(self):
        """RSSParser re-encodes windows-1251 feed when first parse is bozo."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType
        from unittest.mock import patch

        source = ContentSource(
            id=1,
            name="Test",
            slug="test",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        # "выставка" in windows-1251
        cp1251_bytes = "выставка".encode("cp1251")

        broken = {
            "bozo": True,
            "bozo_exception": Exception("invalid encoding"),
            "entries": [],
            "feed": {},
        }
        good = {
            "bozo": False,
            "entries": [
                {
                    "title": "Выставка",
                    "link": "https://example.com/1",
                    "summary": "Описание",
                    "published_parsed": None,
                    "tags": [],
                }
            ],
            "feed": {},
        }

        parser = RSSParser()
        with patch("feedparser.parse", side_effect=[broken, good]) as mock_parse:
            events = await parser.parse(cp1251_bytes, source)

        # Second call used re-encoded UTF-8 bytes
        assert mock_parse.call_count == 2
        assert len(events) == 1
        assert events[0].title == "Выставка"

    @pytest.mark.asyncio
    async def test_parse_relative_link_resolves_to_absolute(self):
        """Относительная ссылка (gorodskoyportal) склеивается с доменом источника.

        Telegram требует абсолютный URL для inline-кнопок, иначе публикация
        падает: 'inline keyboard button URL ... is invalid: URL host is empty'.
        """
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType
        from unittest.mock import patch

        source = ContentSource(
            id=1,
            name="Test",
            slug="test",
            source_type=SourceType.RSS,
            feed_url="https://gorodskoyportal.ru/rostov/afisha/rss/",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Выставка",
                    "link": "/rostov/afisha/poster/1053737/",
                    "summary": "Описание",
                    "published_parsed": None,
                    "tags": [],
                }
            ],
            "feed": {},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert len(events) == 1
        assert events[0].url == "https://gorodskoyportal.ru/rostov/afisha/poster/1053737/"

    @pytest.mark.asyncio
    async def test_parse_absolute_link_unchanged(self):
        """Абсолютная ссылка не меняется при нормализации."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType
        from unittest.mock import patch

        source = ContentSource(
            id=1,
            name="Test",
            slug="test",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Выставка",
                    "link": "https://example.com/event/1",
                    "summary": "Описание",
                    "published_parsed": None,
                    "tags": [],
                }
            ],
            "feed": {},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert events[0].url == "https://example.com/event/1"

    @pytest.mark.asyncio
    async def test_parse_extracts_image_from_enclosure(self):
        """image_url извлекается из links enclosure (gorodskoyportal/Lenta)."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType

        source = ContentSource(
            id=1, name="Test", slug="test",
            source_type=SourceType.RSS, feed_url="https://example.com/rss",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Выставка",
                    "link": "https://example.com/event/1",
                    "summary": "Описание",
                    "published_parsed": None,
                    "tags": [],
                    "links": [
                        {"rel": "enclosure", "type": "image/jpeg",
                         "href": "http://gorodskoyportal.ru/moskva/pictures/posters/1/1_big.jpg"},
                    ],
                }
            ],
            "feed": {},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert events[0].image_url == "http://gorodskoyportal.ru/moskva/pictures/posters/1/1_big.jpg"

    @pytest.mark.asyncio
    async def test_parse_no_image_returns_empty(self):
        """Без картинки image_url пустой."""
        from src.aggregator.parsers.rss_parser import RSSParser
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType

        source = ContentSource(
            id=1, name="Test", slug="test",
            source_type=SourceType.RSS, feed_url="https://example.com/rss",
        )

        mock_feed = {
            "entries": [
                {
                    "title": "Выставка",
                    "link": "https://example.com/event/1",
                    "summary": "Описание",
                    "published_parsed": None,
                    "tags": [],
                }
            ],
            "feed": {},
        }

        parser = RSSParser()
        with patch("feedparser.parse", return_value=mock_feed):
            events = await parser.parse(b"dummy", source)

        assert events[0].image_url == ""
