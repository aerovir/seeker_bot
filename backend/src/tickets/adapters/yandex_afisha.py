"""
Seeker Bot — Yandex Afisha ticket adapter.

Searches for tickets on afisha.yandex.ru.
Uses web scraping since the public API is limited.
"""

import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from src.tickets.base import BaseTicketAdapter
from src.tickets.models import TicketInfo
from src.common.logging import logger


class YandexAfishaAdapter(BaseTicketAdapter):
    """Search tickets on Yandex Afisha."""

    BASE_URL = "https://afisha.yandex.ru"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def search(
        self,
        event_title: str,
        venue: str | None,
        date=None,
    ) -> list[TicketInfo]:
        """Search for tickets on Yandex Afisha."""
        query = event_title
        if venue:
            query += f" {venue}"

        search_url = f"{self.BASE_URL}/search?q={urllib.parse.quote(query[:100])}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; SeekerBot/1.0)",
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        logger.warning("yandex_afisha_http_error", status=response.status)
                        return []

                    html = await response.text()
                    tickets = await self._parse_results(html, search_url)

                    logger.debug(
                        "yandex_afisha_search",
                        query=query[:50],
                        results=len(tickets),
                    )
                    return tickets

        except Exception as e:
            logger.warning("yandex_afisha_error", error=str(e))
            return []

    async def _parse_results(self, html: str, search_url: str) -> list[TicketInfo]:
        """Parse Yandex Afisha search results HTML."""
        soup = BeautifulSoup(html, "lxml")

        tickets: list[TicketInfo] = []
        # Find event cards/links
        event_links = soup.select("a[href*='/event/']")
        price_spans = soup.find_all(string=lambda s: s and "₽" in s if s else False)

        # If we found links, use the first one
        if event_links:
            href = event_links[0].get("href", "")
            if href:
                full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

                price_min = None
                price_max = None
                if price_spans:
                    import re
                    prices = re.findall(r"(\d+)", price_spans[0])
                    if len(prices) >= 2:
                        price_min = float(prices[0])
                        price_max = float(prices[1])
                    elif prices:
                        price_min = float(prices[0])

                tickets.append(TicketInfo(
                    url=full_url,
                    provider="yandex_afisha",
                    provider_name="Яндекс Афиша",
                    price_min=price_min,
                    price_max=price_max,
                ))

        # Fallback: return search page URL
        if not tickets:
            tickets.append(TicketInfo(
                url=search_url,
                provider="yandex_afisha",
                provider_name="Яндекс Афиша",
            ))

        return tickets

    async def get_event_url(
        self,
        event_title: str,
        venue: str | None,
    ) -> str | None:
        """Get search URL for event on Yandex Afisha."""
        query = event_title[:50]
        return f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"
