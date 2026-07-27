"""
Seeker Bot — Event enricher.

Adds ticket links, prices, and images to raw events.
Currently returns the event as-is; ticket adapters will be added in Phase 3.
"""

from src.aggregator.models import RawEvent, EnrichedEvent
from src.common.logging import logger


class Enricher:
    """Enriches raw events with ticket and price data."""

    def __init__(self, session=None):
        self.session = session

    def enrich_all(self, events: list[RawEvent]) -> list[EnrichedEvent]:
        """Enrich a list of raw events.

        Currently converts RawEvent -> EnrichedEvent with basic processing.
        Phase 3 will add ticket adapter lookups.

        Args:
            events: List of RawEvent objects.

        Returns:
            List of EnrichedEvent objects.
        """
        enriched = []
        for raw in events:
            enriched_event = EnrichedEvent.from_raw(raw)
            enriched_event = self._extract_prices(enriched_event, raw)
            enriched.append(enriched_event)

        logger.debug("enrichment_complete", count=len(enriched))
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
