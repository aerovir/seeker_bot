"""
Tests for TicketAdapter base and provider implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTicketAdapterBase:
    @pytest.mark.asyncio
    async def test_ticket_info_dataclass(self):
        """TicketInfo can be created with all fields."""
        from src.tickets.models import TicketInfo

        info = TicketInfo(
            url="https://example.com/ticket",
            provider="yandex_afisha",
            provider_name="Яндекс Афиша",
            price_min=500.0,
            price_max=1000.0,
            currency="RUB",
            availability="available",
        )
        assert info.url == "https://example.com/ticket"
        assert info.provider == "yandex_afisha"
        assert info.price_min == 500.0
        assert info.availability == "available"

    @pytest.mark.asyncio
    async def test_ticket_info_defaults(self):
        """TicketInfo has sensible defaults."""
        from src.tickets.models import TicketInfo

        info = TicketInfo(url="https://example.com", provider="test", provider_name="Test")
        assert info.currency == "RUB"
        assert info.availability == "available"
        assert info.price_min is None

    @pytest.mark.asyncio
    async def test_adapter_base_cannot_instantiate(self):
        """BaseTicketAdapter cannot be instantiated directly."""
        from src.tickets.base import BaseTicketAdapter

        with pytest.raises(TypeError):
            BaseTicketAdapter()


class TestDirectLinkAdapter:
    @pytest.mark.asyncio
    async def test_search_no_venue(self):
        """DirectLinkAdapter generates link from title only."""
        import urllib.parse
        from src.tickets.adapters.direct_link import DirectLinkAdapter

        adapter = DirectLinkAdapter()
        tickets = await adapter.search("Выставка Айвазовского", None, None)

        assert len(tickets) == 1
        assert tickets[0].provider == "direct_link"
        decoded = urllib.parse.unquote(tickets[0].url)
        assert "Выставка Айвазовского" in decoded

    @pytest.mark.asyncio
    async def test_search_with_venue(self):
        """DirectLinkAdapter generates link with venue."""
        import urllib.parse
        from src.tickets.adapters.direct_link import DirectLinkAdapter

        adapter = DirectLinkAdapter()
        tickets = await adapter.search("Спектакль", "Большой театр", None)

        assert len(tickets) == 1
        decoded = urllib.parse.unquote(tickets[0].url)
        assert "Большой" in decoded

    @pytest.mark.asyncio
    async def test_get_event_url(self):
        """DirectLinkAdapter returns search URL."""
        import urllib.parse
        from src.tickets.adapters.direct_link import DirectLinkAdapter

        adapter = DirectLinkAdapter()
        url = await adapter.get_event_url("Выставка", None)
        assert url is not None
        decoded = urllib.parse.unquote(url)
        assert "Выставка" in decoded


class TestYandexAfishaAdapter:
    @pytest.mark.asyncio
    async def test_search_success(self):
        """YandexAfishaAdapter returns tickets on success."""
        from src.tickets.adapters.yandex_afisha import YandexAfishaAdapter

        adapter = YandexAfishaAdapter(api_key="test_key")
        mock_html = """
        <html>
            <div class="event-card">
                <a class="button" href="/event/123">Купить билеты</a>
                <span class="price">500-1000 ₽</span>
            </div>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.text.return_value = mock_html

        mock_get = MagicMock(return_value=mock_response)
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value.get = mock_get

        with patch("aiohttp.ClientSession", return_value=mock_session):
            tickets = await adapter.search("Выставка", "Музей", None)

        assert len(tickets) > 0
        assert tickets[0].provider == "yandex_afisha"

    @pytest.mark.asyncio
    async def test_search_error(self):
        """YandexAfishaAdapter returns empty on HTTP error."""
        from src.tickets.adapters.yandex_afisha import YandexAfishaAdapter

        adapter = YandexAfishaAdapter(api_key="test_key")

        mock_get = MagicMock(side_effect=Exception("HTTP error"))
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value.get = mock_get

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("src.tickets.adapters.yandex_afisha.logger"):
            tickets = await adapter.search("Выставка", None, None)

        assert tickets == []

    @pytest.mark.asyncio
    async def test_get_event_url(self):
        """YandexAfishaAdapter returns search URL."""
        from src.tickets.adapters.yandex_afisha import YandexAfishaAdapter

        adapter = YandexAfishaAdapter()
        url = await adapter.get_event_url("Выставка", "Музей")
        assert url is not None
        assert "afisha.yandex.ru" in url


class TestEnricherTicketIntegration:
    @pytest.mark.asyncio
    async def test_enricher_with_ticket_adapters(self):
        """Enricher uses ticket adapters to find tickets (async)."""
        from src.aggregator.enricher import Enricher
        from src.aggregator.models import RawEvent
        import asyncio

        raw = RawEvent(
            title="Выставка в Москве",
            description="Тестовая выставка",
            content_source_id=1,
            source_slug="test",
            source_item_guid="guid-1",
            venue_name="Галерея",
            start_date=None,
        )

        enricher = Enricher(session=None)

        # Mock enrich_tickets to do nothing and return the enriched event
        original_fn = enricher._enrich_tickets
        async def mock_enrich(enriched, raw_event, adapters=None):
            return enriched
        enricher._enrich_tickets = mock_enrich

        enriched = await enricher.enrich_all([raw])

        assert len(enriched) == 1
        assert enriched[0].title == "Выставка в Москве"

    @pytest.mark.asyncio
    async def test_enrich_tickets(self):
        """_enrich_tickets tries adapters and sets ticket data."""
        from src.aggregator.enricher import Enricher
        from src.aggregator.models import RawEvent, EnrichedEvent
        from src.tickets.models import TicketInfo

        raw = RawEvent(
            title="Выставка", description="Описание", content_source_id=1,
            source_slug="test", source_item_guid="guid-1",
            venue_name="Музей",
        )
        enriched = EnrichedEvent.from_raw(raw)

        mock_adapter = MagicMock()
        mock_adapter.search = AsyncMock(return_value=[
            TicketInfo(
                url="https://tickets.com/event",
                provider="yandex_afisha",
                provider_name="Яндекс Афиша",
                price_min=500.0,
                price_max=1000.0,
            ),
        ])

        enricher = Enricher(session=None)
        await enricher._enrich_tickets(enriched, raw, adapters=[mock_adapter])

        assert enriched.ticket_url == "https://tickets.com/event"
        assert enriched.ticket_provider == "Яндекс Афиша"
        assert enriched.price_min == 500.0
        assert enriched.price_max == 1000.0

    @pytest.mark.asyncio
    async def test_enrich_tickets_no_results(self):
        """_enrich_tickets leaves event unchanged when no tickets found."""
        from src.aggregator.enricher import Enricher
        from src.aggregator.models import RawEvent, EnrichedEvent

        raw = RawEvent(
            title="Выставка", description="Описание", content_source_id=1,
            source_slug="test", source_item_guid="guid-1",
        )
        enriched = EnrichedEvent.from_raw(raw)

        mock_adapter = MagicMock()
        mock_adapter.search = AsyncMock(return_value=[])

        enricher = Enricher(session=None)
        await enricher._enrich_tickets(enriched, raw, adapters=[mock_adapter])

        assert enriched.ticket_url is None
        assert enriched.ticket_provider is None
