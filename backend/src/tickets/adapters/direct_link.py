"""
Seeker Bot — Direct link ticket adapter.

Generates a search URL for a general search engine as fallback.
"""

import urllib.parse

from src.tickets.base import BaseTicketAdapter
from src.tickets.models import TicketInfo
from src.common.logging import logger


class DirectLinkAdapter(BaseTicketAdapter):
    """Fallback adapter: generates a generic search URL."""

    SEARCH_URL = "https://yandex.ru/search/?text="

    async def search(
        self,
        event_title: str,
        venue: str | None,
        date=None,
    ) -> list[TicketInfo]:
        """Generate a search link as a fallback ticket option."""
        query = event_title
        if venue:
            query += f" {venue}"
        query += " купить билеты"

        encoded = urllib.parse.quote(query)
        url = f"{self.SEARCH_URL}{encoded}"

        logger.debug(
            "direct_link_search",
            query=query,
        )

        return [
            TicketInfo(
                url=url,
                provider="direct_link",
                provider_name="Поиск билетов",
            )
        ]

    async def get_event_url(
        self,
        event_title: str,
        venue: str | None,
    ) -> str | None:
        """Get search URL for event."""
        query = event_title
        if venue:
            query += f" {venue}"
        query += " билеты"
        encoded = urllib.parse.quote(query)
        return f"{self.SEARCH_URL}{encoded}"
