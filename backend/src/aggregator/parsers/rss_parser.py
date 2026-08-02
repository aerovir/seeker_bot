"""
Seeker Bot — RSS/Atom feed parser.

Converts RSS/Atom feed data into RawEvent objects using feedparser.
"""

import hashlib

import feedparser

from src.aggregator.parsers.base import BaseParser
from src.aggregator.models import RawEvent
from src.common.exceptions import ParseError
from src.common.logging import logger


class RSSParser(BaseParser):
    """Parses RSS/Atom feed XML into RawEvent objects."""

    async def parse(self, raw_data: bytes, source) -> list[RawEvent]:
        """Parse RSS/Atom XML into RawEvent list.

        Args:
            raw_data: RSS/Atom XML bytes.
            source: ContentSource model instance.

        Returns:
            List of RawEvent objects.

        Raises:
            ParseError: If the feed is malformed.
        """
        feed = feedparser.parse(raw_data)

        # Legacy feeds (windows-1251) sometimes fail encoding auto-detection.
        # Re-encode to UTF-8 and retry once before giving up.
        if feed.get("bozo") and feed.get("bozo_exception"):
            try:
                text = raw_data.decode("cp1251", errors="replace")
                utf8_data = text.encode("utf-8")
                feed = feedparser.parse(utf8_data)
            except Exception:
                pass

        if feed.get("bozo") and feed.get("bozo_exception"):
            error = feed["bozo_exception"]
            logger.warning("rss_parse_error", error=str(error))
            raise ParseError(f"RSS parse error: {error}")

        events: list[RawEvent] = []
        for entry in feed.get("entries", []):
            event = self._entry_to_raw(entry, source)
            events.append(event)

        logger.debug(
            "rss_parse_complete",
            source=source.slug if source else "unknown",
            count=len(events),
        )
        return events

    def _entry_to_raw(self, entry: dict, source) -> RawEvent:
        """Convert a feedparser entry dict to RawEvent."""
        title = entry.get("title") or ""
        link = entry.get("link") or ""
        # Некоторые источники (gorodskoyportal) отдают относительные ссылки
        # (/rostov/afisha/poster/123/) — Telegram требует абсолютный URL для
        # inline-кнопок. Склеиваем с доменом из feed_url источника.
        if link.startswith("/") and source is not None and source.feed_url:
            from urllib.parse import urlsplit, urlunsplit

            parts = urlsplit(source.feed_url)
            link = urlunsplit((parts.scheme, parts.netloc, link, "", ""))
        summary = entry.get("summary") or entry.get("description") or ""

        # Build a stable GUID
        guid = entry.get("id") or link
        item_hash = hashlib.sha256(f"{title}:{guid}".encode()).hexdigest()

        # Extract published date
        start_date = None
        published = entry.get("published_parsed")
        if published:
            import time
            from datetime import datetime, timezone

            start_date = datetime.fromtimestamp(time.mktime(published), tz=timezone.utc)

        # Extract categories from RSS tags
        categories: list[tuple[int, float, str]] = []
        for tag in entry.get("tags", []):
            term = tag.get("term", "")
            if term:
                categories.append((0, 0.5, "rss_tag"))

        source_slug = source.slug if source else "unknown"
        source_id = source.id if source else 0
        source_url = source.feed_url if source else None

        return RawEvent(
            title=title,
            description=summary,
            content_source_id=source_id,
            source_slug=source_slug,
            source_item_guid=item_hash,
            source_url=source_url,
            url=link,
            image_url=self._extract_image(entry),
            start_date=start_date,
            categories=categories,
        )

    @staticmethod
    def _extract_image(entry: dict) -> str:
        """Extract an image URL from an RSS entry.

        Приоритет: links enclosure (image/*) → media_content → media_thumbnail.
        gorodskoyportal и Lenta отдают фото через links rel=enclosure.
        """
        # 1. links / enclosure
        for link in entry.get("links", []):
            rel = link.get("rel", "")
            link_type = link.get("type", "") or ""
            href = link.get("href", "")
            if rel == "enclosure" and link_type.startswith("image/") and href:
                return href
        # 2. media_content
        for mc in entry.get("media_content", []):
            url = mc.get("url", "")
            if url:
                return url
        # 3. media_thumbnail
        for mt in entry.get("media_thumbnail", []):
            url = mt.get("url", "")
            if url:
                return url
        return ""
