"""
Seeker Bot — Venue scraper.

Извлекает название места и адрес с HTML-страницы события.
gorodskoyportal размечает страницы через Schema.org микроразметку
(itemprop="location" → name, address → streetAddress + addressLocality).
Страницы отдаются в windows-1251.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlsplit

from src.common.logging import logger

GORODSKOY_PORTAL = "gorodskoyportal.ru"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT_SECONDS = 8


class VenueInfo:
    """Parsed venue data for an event."""

    __slots__ = ("name", "address")

    def __init__(self, name: str = "", address: str = ""):
        self.name = name
        self.address = address


async def scrape_venue(url: str, session: aiohttp.ClientSession | None = None) -> VenueInfo | None:
    """Scrape venue name and address from an event page.

    Работает только для gorodskoyportal (у остальных источников на странице
    нет Schema.org микроразметки места). Fail-safe: любая ошибка → None,
    чтобы публикация/парсинг не падали из-за недоступной страницы.
    """
    if not url:
        return None

    try:
        host = urlsplit(url).netloc
    except ValueError:
        return None

    if GORODSKOY_PORTAL not in host:
        return None

    try:
        return await _fetch_and_parse(url, session)
    except Exception as e:
        logger.warning("venue_scrape_error", url=url, error=str(e))
        return None


async def _fetch_and_parse(url: str, session: aiohttp.ClientSession | None) -> VenueInfo:
    async def _get() -> bytes:
        if session is not None:
            async with session.get(url, timeout=aiohttp.ClientTimeout(TIMEOUT_SECONDS)) as resp:
                return await resp.read()
        async with aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT}
        ) as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(TIMEOUT_SECONDS)) as resp:
                return await resp.read()

    data = await _get()
    html = data.decode("windows-1251", errors="replace")
    return _parse_venue(html)


def _parse_venue(html: str) -> VenueInfo | None:
    """Parse Schema.org microdata from gorodskoyportal event HTML."""
    soup = BeautifulSoup(html, "lxml")

    location = soup.find(attrs={"itemprop": "location"})
    if not location:
        return None

    venue = VenueInfo()

    # Название места: <span itemprop="name"> внутри location
    name_el = location.find(attrs={"itemprop": "name"})
    if name_el:
        venue.name = name_el.get_text(strip=True)

    # Адрес: <span itemprop="address"> → streetAddress + addressLocality
    address_el = location.find(attrs={"itemprop": "address"})
    if address_el:
        street = _text_of(address_el, "streetAddress")
        city = _text_of(address_el, "addressLocality")
        parts = [p for p in (street, city) if p]
        if parts:
            venue.address = ", ".join(parts)

    # Ничего не нашли — считаем невалидным
    if not venue.name and not venue.address:
        return None

    return venue


def _text_of(el, itemprop: str) -> str:
    node = el.find(attrs={"itemprop": itemprop})
    if node:
        return node.get_text(strip=True)
    return ""
