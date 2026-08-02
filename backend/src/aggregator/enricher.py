"""
Seeker Bot — Event enricher.

Adds ticket links, prices, and images to raw events.
Integrates with ticket adapters (Yandex Afisha, Kassir, etc.).
"""

import asyncio
from urllib.parse import urlsplit

from src.aggregator.models import RawEvent, EnrichedEvent
from src.aggregator.scrapers.venue_scraper import scrape_venue
from src.tickets.adapters import YandexAfishaAdapter, KassirAdapter, DirectLinkAdapter
from src.common.logging import logger


DEFAULT_ADAPTERS = [
    YandexAfishaAdapter(),
    KassirAdapter(),
    DirectLinkAdapter(),
]

# Максимум параллельных запросов к страницам событий при скрейпинге места
VENUE_SCRAPE_CONCURRENCY = 5


class Enricher:
    """Enriches raw events with ticket and price data."""

    def __init__(self, session=None, ticket_adapters=None):
        self.session = session
        self.ticket_adapters = ticket_adapters or DEFAULT_ADAPTERS

    async def enrich_all(self, events: list[RawEvent]) -> list[EnrichedEvent]:
        """Enrich a list of raw events with tickets and prices.

        Args:
            events: List of RawEvent objects.

        Returns:
            List of EnrichedEvent objects.
        """
        enriched = []
        for raw in events:
            enriched_event = EnrichedEvent.from_raw(raw)
            enriched_event = self._extract_prices(enriched_event, raw)
            await self._enrich_tickets(enriched_event, raw, self.ticket_adapters)
            enriched.append(enriched_event)

        # Параллельный скрейпинг места/адреса (только gorodskoyportal)
        await self._enrich_venues(enriched)

        logger.debug("enrichment_complete", count=len(enriched))
        return enriched

    async def _enrich_venues(self, events: list[EnrichedEvent]) -> None:
        """Заполнить venue_name/venue_address скрейпингом страниц события.

        Параллельно с ограничением, fail-safe: недоступная страница не
        роняет парсинг. Пропускаем события, у которых место уже есть.
        """
        to_scrape = [
            e for e in events
            if e.url and "gorodskoyportal" in urlsplit(e.url).netloc
            and not e.venue_name
        ]
        if not to_scrape:
            return

        sem = asyncio.Semaphore(VENUE_SCRAPE_CONCURRENCY)

        async def _scrape_one(event: EnrichedEvent) -> None:
            async with sem:
                venue = await scrape_venue(event.url)
                if venue:
                    event.venue_name = venue.name or event.venue_name
                    event.venue_address = venue.address or event.venue_address

        results = await asyncio.gather(
            *(_scrape_one(e) for e in to_scrape),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.warning("venue_enrich_error", error=str(r))

    async def _enrich_tickets(
        self,
        enriched: EnrichedEvent,
        raw: RawEvent,
        adapters: list | None = None,
    ) -> EnrichedEvent:
        """Try each ticket adapter to find tickets for this event."""
        adapters = adapters or self.ticket_adapters

        for adapter in adapters:
            try:
                tickets = await adapter.search(
                    raw.title,
                    raw.venue_name,
                    raw.start_date,
                )
                if tickets:
                    best = tickets[0]
                    enriched.ticket_url = best.url
                    enriched.ticket_provider = best.provider_name
                    if best.price_min is not None:
                        enriched.price_min = best.price_min
                        enriched.price_max = best.price_max
                    break
            except Exception as e:
                logger.warning(
                    "ticket_adapter_error",
                    adapter=adapter.__class__.__name__,
                    error=str(e),
                )
                continue

        return enriched

    @staticmethod
    def _extract_prices(enriched: EnrichedEvent, raw: RawEvent) -> EnrichedEvent:
        """Extract price information from raw event text."""
        if not raw.price_text:
            return enriched

        import re

        text = raw.price_text

        # Pattern: 500-1000 руб / 500 руб
        price_pattern = r"(\d+(?:\s*\d+)?)\s*(?:-|–|—)\s*(\d+(?:\s*\d+)?)\s*(?:р(?:уб)?\.?)"
        match = re.search(price_pattern, text, re.IGNORECASE)
        if match:
            enriched.price_min = float(match.group(1).replace(" ", ""))
            enriched.price_max = float(match.group(2).replace(" ", ""))
            return enriched

        # Pattern: от 500 руб
        single_pattern = r"(?:от\s*)?(\d+(?:\s*\d+)?)\s*(?:р(?:уб)?\.?|₽)"
        match = re.search(single_pattern, text, re.IGNORECASE)
        if match:
            enriched.price_min = float(match.group(1).replace(" ", ""))
            return enriched

        return enriched
