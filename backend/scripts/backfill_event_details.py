#!/usr/bin/env python3
"""
Seeker Bot — Backfill event details (image_url, venue) for existing events.

Разовый скрипт для событий, сохранённых до добавления извлечения фото и
скрейпинга места. Заполняет:
- image_url — из RSS gorodskoyportal источников (links enclosure)
- venue_name / venue_address — скрейпингом Schema.org с HTML страницы

Использование:
    python scripts/backfill_event_details.py            # все события
    python scripts/backfill_event_details.py --limit 50 # только 50
"""

import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp
import feedparser
from sqlalchemy import select

from src.db.session import async_session_factory
from src.db.models.source import ContentSource
from src.db.models.event import Event
from src.aggregator.scrapers.venue_scraper import scrape_venue, GORODSKOY_PORTAL
from src.common.logging import logger

CONCURRENCY = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


async def _fetch(url: str, session) -> bytes:
    async with session.get(url, timeout=aiohttp.ClientTimeout(20)) as resp:
        return await resp.read()


async def backfill_images_from_rss(limit: int | None = None) -> int:
    """Заполнить image_url из RSS-лент gorodskoyportal по external_id."""
    updated = 0
    async with async_session_factory() as session:
        result = await session.execute(
            select(ContentSource).where(ContentSource.feed_url.like(f"%{GORODSKOY_PORTAL}%"))
        )
        sources = list(result.scalars().all())

        async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as http:
            for source in sources:
                try:
                    data = await _fetch(source.feed_url, http)
                    feed = feedparser.parse(data)
                except Exception as e:
                    logger.warning("backfill_fetch_error", source=source.slug, error=str(e))
                    continue

                for entry in feed.entries:
                    if limit is not None and updated >= limit:
                        return updated

                    title = entry.get("title") or ""
                    guid = entry.get("id") or entry.get("link") or ""
                    item_hash = hashlib.sha256(f"{title}:{guid}".encode()).hexdigest()
                    external_id = f"{source.slug}:{item_hash}"

                    image = ""
                    for link in entry.get("links", []):
                        if (link.get("rel") == "enclosure"
                                and (link.get("type") or "").startswith("image/")
                                and link.get("href")):
                            image = link["href"]
                            break
                    if not image:
                        continue

                    event = await session.scalar(
                        select(Event).where(Event.external_id == external_id)
                    )
                    if event and not event.image_url:
                        event.image_url = image
                        updated += 1

            await session.commit()
    return updated


async def backfill_venues(limit: int | None = None) -> int:
    """Заполнить venue_name/venue_address скрейпингом страниц событий."""
    updated = 0
    async with async_session_factory() as session:
        result = await session.execute(
            select(Event).where(
                (Event.venue_name.is_(None) | (Event.venue_name == "")),
                Event.url.like(f"%{GORODSKOY_PORTAL}%"),
            ).limit(limit or 100000)
        )
        events = list(result.scalars().all())

        if not events:
            logger.info("backfill_no_events_to_scrape")
            return 0

        sem = asyncio.Semaphore(CONCURRENCY)

        async def _scrape_one(event: Event) -> None:
            nonlocal updated
            async with sem:
                venue = await scrape_venue(event.url)
                if venue and (venue.name or venue.address):
                    event.venue_name = venue.name or None
                    event.venue_address = venue.address or None
                    updated += 1

        await asyncio.gather(*(_scrape_one(e) for e in events), return_exceptions=True)
        await session.commit()
    return updated


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Backfill event details")
    parser.add_argument("--limit", "-l", type=int, default=None,
                        help="Ограничить количество обработанных событий")
    args = parser.parse_args()

    print("1/2 Заполнение image_url из RSS...")
    images = await backfill_images_from_rss(args.limit)
    print(f"   Обновлено image_url: {images}")

    print("2/2 Скрейпинг места/адреса...")
    venues = await backfill_venues(args.limit)
    print(f"   Обновлено venue: {venues}")

    print("\n✅ Backfill завершён")


if __name__ == "__main__":
    asyncio.run(main())
