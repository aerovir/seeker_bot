"""
Seeker Bot — Event validator.

Проверяет, что событие «живое», перед публикацией в канал.
Основной канал сверки — повторное чтение RSS-источника события: если
запись с тем же external_id (guid) всё ещё есть в ленте — событие живо.
Дополнительно — проверка живости страницы события и обогащение
недостающих полей (описание, фото, место) из найденного источника.
"""

import asyncio
import hashlib
import html
import urllib.parse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from src.aggregator.scrapers.venue_scraper import scrape_venue, GORODSKOY_PORTAL
from src.common.logging import logger
from src.db.models.event import Event

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
RSS_TIMEOUT = 20
PAGE_TIMEOUT = 8


class ValidationResult:
    """Результат валидации события."""

    __slots__ = (
        "valid", "source", "description", "short_description",
        "image_url", "venue_name", "venue_address",
    )

    def __init__(
        self,
        valid: bool = False,
        source: str = "",
        description: str | None = None,
        short_description: str | None = None,
        image_url: str | None = None,
        venue_name: str | None = None,
        venue_address: str | None = None,
    ):
        self.valid = valid
        self.source = source
        self.description = description
        self.short_description = short_description
        self.image_url = image_url
        self.venue_name = venue_name
        self.venue_address = venue_address


def html_to_text(value: str | None) -> str:
    """Конвертировать HTML-описание в чистый текст."""
    if not value:
        return ""
    soup = BeautifulSoup(value, "lxml")
    text = soup.get_text(" ", strip=True)
    return html.unescape(text)


async def _fetch_bytes(url: str, session: aiohttp.ClientSession, timeout: int) -> bytes:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
        return await resp.read()


async def validate_event(session: AsyncSession, event: Event) -> ValidationResult:
    """Сверить событие с источниками и вернуть результат + данные для обогащения.

    Args:
        session: AsyncSession (не используется напрямую, но для совместимости).
        event: Событие для проверки.

    Returns:
        ValidationResult: valid=True если событие найдено и живо.
    """
    if not event.source:
        return ValidationResult(valid=False, source="no-source")

    # external_id = "{source.slug}:{guid_hash}"
    parts = (event.external_id or "").split(":", 1)
    guid_hash = parts[1] if len(parts) > 1 else ""

    headers = {"User-Agent": USER_AGENT}
    async with aiohttp.ClientSession(headers=headers) as http:
        # 1. Сверка с RSS-источником
        try:
            data = await _fetch_bytes(event.source.feed_url, http, RSS_TIMEOUT)
            feed = feedparser.parse(data)

            entries = feed.get("entries", []) if isinstance(feed, dict) else feed.entries
            for entry in entries:
                title = entry.get("title") or ""
                guid = entry.get("id") or entry.get("link") or ""
                item_hash = hashlib.sha256(f"{title}:{guid}".encode()).hexdigest()

                if item_hash == guid_hash:
                    # Событие живо в RSS — собираем данные для обогащения
                    result = ValidationResult(
                        valid=True,
                        source="rss",
                        description=entry.get("summary") or entry.get("description"),
                        short_description=html_to_text(
                            entry.get("summary") or entry.get("description")
                        ),
                    )
                    # Фото из links
                    for link in entry.get("links", []):
                        if (link.get("rel") == "enclosure"
                                and (link.get("type") or "").startswith("image/")
                                and link.get("href")):
                            result.image_url = link["href"]
                            break
                    # Место со страницы события
                    if event.url and GORODSKOY_PORTAL in urllib.parse.urlsplit(event.url).netloc:
                        venue = await scrape_venue(event.url, http)
                        if venue:
                            result.venue_name = venue.name
                            result.venue_address = venue.address
                    return result
        except Exception as e:
            logger.warning("validator_rss_error", source=event.source.slug, error=str(e))

        # 2. Проверка живости страницы события (если URL есть)
        if event.url:
            try:
                await _fetch_bytes(event.url, http, PAGE_TIMEOUT)
                # Страница жива — событие существует
                result = ValidationResult(
                    valid=True,
                    source="page",
                    description=event.description,
                    short_description=html_to_text(event.description),
                )
                if event.url and GORODSKOY_PORTAL in urllib.parse.urlsplit(event.url).netloc:
                    venue = await scrape_venue(event.url, http)
                    if venue:
                        result.venue_name = venue.name
                        result.venue_address = venue.address
                return result
            except Exception:
                pass  # 404 — событие снято

    # Не нашли ни в RSS, ни на живой странице
    logger.info("validator_event_not_found", event_id=event.id, title=event.title[:50])
    return ValidationResult(valid=False, source="none")
