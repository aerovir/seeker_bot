"""
Tests for VenueScraper — Schema.org venue extraction from event pages.
"""

import pytest


class TestVenueScraper:
    def test_parse_schema_org_venue(self):
        """Извлекает название места и адрес из Schema.org микроразметки."""
        from src.aggregator.scrapers.venue_scraper import _parse_venue

        html = """
        <html><body>
        <div class="event" itemscope itemtype="http://schema.org/Event">
          <p itemprop="location" itemscope itemtype="http://schema.org/Place">
            <a itemprop="url" href="/moskva/afisha/place/59822/">
              <span itemprop="name">StandUp Store Moscow</span>
            </a>
            <span style="display:none;" itemprop="address" itemscope itemtype="http://schema.org/PostalAddress">
              <span itemprop="addressLocality">Москва</span>
              <span itemprop="streetAddress">ул. Петровка, 21</span>
            </span>
          </p>
        </div>
        </body></html>
        """

        venue = _parse_venue(html)
        assert venue is not None
        assert venue.name == "StandUp Store Moscow"
        assert venue.address == "ул. Петровка, 21, Москва"

    def test_parse_no_location_returns_none(self):
        """Без микроразметки места — None."""
        from src.aggregator.scrapers.venue_scraper import _parse_venue

        html = "<html><body><p>Обычный текст</p></body></html>"
        assert _parse_venue(html) is None

    @pytest.mark.asyncio
    async def test_scrape_venue_skips_non_gorodskoyportal(self):
        """Для не-gorodskoyportal URL скрейпинг не выполняется."""
        from src.aggregator.scrapers.venue_scraper import scrape_venue

        assert await scrape_venue("https://lenta.ru/news/123") is None

    @pytest.mark.asyncio
    async def test_scrape_venue_network_error_returns_none(self):
        """Ошибка сети → None (fail-safe), а не исключение."""
        from unittest.mock import patch
        from src.aggregator.scrapers.venue_scraper import scrape_venue

        with patch(
            "src.aggregator.scrapers.venue_scraper._fetch_and_parse",
            side_effect=Exception("timeout"),
        ):
            result = await scrape_venue("https://gorodskoyportal.ru/moskva/afisha/poster/1/")
        assert result is None
