"""
Seeker Bot — Kassir.ru ticket adapter.

Searches for tickets on kassir.ru via web scraping.
"""

import urllib.parse
import re

import aiohttp
from bs4 import BeautifulSoup

from src.tickets.base import BaseTicketAdapter
from src.tickets.models import TicketInfo
from src.common.logging import logger


class KassirAdapter(BaseTicketAdapter):
    """Search tickets on Kassir.ru."""

    BASE_URL = "https://kassir.ru"

    async def search(
        self,
        event_title: str,
        venue: str | None,
        date=None,
    ) -> list[TicketInfo]:
        """Search for tickets on Kassir.ru."""
        query = event_title[:80]
        search_url = f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; SeekerBot/1.0)",
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        logger.warning("kassir_http_error", status=response.status)
                        return []

                    html = await response.text()
                    tickets = self._parse_results(html)

                    logger.debug(
                        "kassir_search",
                        query=query[:50],
                        results=len(tickets),
                    )
                    return tickets

        except Exception as e:
            logger.warning("kassir_error", error=str(e))
            return []

    def _parse_results(self, html: str) -> list[TicketInfo]:
        """Parse Kassir.ru search results."""
        soup = BeautifulSoup(html, "lxml")
        tickets: list[TicketInfo] = []

        # Look for event items/cards
        event_items = soup.select("a[href*='/event/'], a[href*='/msk/'], a[href*='/spb/']")
        found_urls: set[str] = set()

        for item in event_items[:5]:
            href = item.get("href", "")
            if not href:
                continue

            full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
            if full_url in found_urls:
                continue
            found_urls.add(full_url)

            # Try to extract price from surrounding text
            price_text = item.get_text()
            prices = re.findall(r"(\d+)\s*(?:₽|руб)", price_text)
            price_min = float(prices[0]) if prices else None

            tickets.append(TicketInfo(
                url=full_url,
                provider="kassir",
                provider_name="Кассир.ру",
                price_min=price_min,
            ))

        # Fallback
        if not tickets:
            tickets.append(TicketInfo(
                url=self.BASE_URL + "/search?q=" + urllib.parse.quote("билеты"),
                provider="kassir",
                provider_name="Кассир.ру",
            ))

        return tickets

    async def get_event_url(
        self,
        event_title: str,
        venue: str | None,
    ) -> str | None:
        """Get search URL for event on Kassir.ru."""
        query = event_title[:50]
        return f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"
