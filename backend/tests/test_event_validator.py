"""
Tests for EventValidator — event liveness validation before publishing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace


class TestHtmlToText:
    def test_html_to_text_strips_tags(self):
        """HTML-описание конвертируется в чистый текст с сущностями."""
        from src.aggregator.validators.event_validator import html_to_text

        text = html_to_text("<p>&laquo;Комикессы&raquo; &mdash; это стендап</p>")
        assert "«Комикессы»" in text
        assert "<p>" not in text
        assert "&mdash;" not in text

    def test_html_to_text_empty(self):
        """Пустое значение → пустая строка."""
        from src.aggregator.validators.event_validator import html_to_text

        assert html_to_text(None) == ""
        assert html_to_text("") == ""


def _make_event(external_id="src:guid_hash"):
    """Создать mock события с источником."""
    source = MagicMock()
    source.feed_url = "https://gorodskoyportal.ru/moskva/afisha/rss/"

    event = MagicMock()
    event.external_id = external_id
    event.source = source
    event.url = "https://gorodskoyportal.ru/moskva/afisha/poster/1/"
    event.description = "<p>Описание события</p>"
    event.title = "Тест"
    event.id = 1
    return event


class TestValidateEvent:
    @pytest.mark.asyncio
    async def test_validates_found_in_rss(self):
        """Событие найдено в RSS → valid, обогащено."""
        import hashlib
        from src.aggregator.validators.event_validator import validate_event

        event = _make_event(external_id=f"afisha-moskva:{'x' * 64}")
        # guid_hash совпадает с тем, что возвращает RSS
        event.external_id = f"afisha-moskva:{'a' * 64}"
        title = "Выставка"
        guid = "https://gorodskoyportal.ru/moskva/afisha/poster/1/"
        item_hash = hashlib.sha256(f"{title}:{guid}".encode()).hexdigest()
        event.external_id = f"afisha-moskva:{item_hash}"

        mock_feed = {
            "entries": [
                {
                    "title": title,
                    "id": guid,
                    "link": guid,
                    "summary": "<p>Описание выставки</p>",
                    "links": [
                        {"rel": "enclosure", "type": "image/jpeg",
                         "href": "http://gorodskoyportal.ru/1.jpg"},
                    ],
                }
            ],
        }

        async def _fake_fetch(url, session, timeout):
            return b"dummy"

        with patch("feedparser.parse", return_value=mock_feed), \
             patch("src.aggregator.validators.event_validator._fetch_bytes",
                   side_effect=_fake_fetch), \
             patch("src.aggregator.validators.event_validator.scrape_venue",
                   return_value=SimpleNamespace(name="Зал", address="ул. Тест, 1")):
            result = await validate_event(AsyncMock(), event)

        assert result.valid is True
        assert result.source == "rss"
        assert result.short_description == "Описание выставки"
        assert result.image_url == "http://gorodskoyportal.ru/1.jpg"
        assert result.venue_name == "Зал"
        assert result.venue_address == "ул. Тест, 1"

    @pytest.mark.asyncio
    async def test_not_found_in_rss(self):
        """События нет в RSS → not valid."""
        from src.aggregator.validators.event_validator import validate_event

        event = _make_event()
        mock_feed = {
            "entries": [
                {"title": "Другое", "id": "other", "link": "other",
                 "summary": ""},
            ],
        }

        with patch("feedparser.parse", return_value=mock_feed), \
             patch("src.aggregator.validators.event_validator._fetch_bytes",
                   side_effect=Exception("404")):
            result = await validate_event(AsyncMock(), event)

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_page_live_fallback(self):
        """В RSS нет, но страница жива → valid (источник page)."""
        from src.aggregator.validators.event_validator import validate_event

        event = _make_event()
        mock_feed = {"entries": []}

        with patch("feedparser.parse", return_value=mock_feed), \
             patch("src.aggregator.validators.event_validator._fetch_bytes",
                   side_effect=[b"rss-dummy", b"page-html"]), \
             patch("src.aggregator.validators.event_validator.scrape_venue",
                   return_value=SimpleNamespace(name="Зал", address="ул. Тест")):
            result = await validate_event(AsyncMock(), event)

        assert result.valid is True
        assert result.source == "page"
        assert result.short_description == "Описание события"
