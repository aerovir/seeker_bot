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
            start_date=start_date,
            categories=categories,
        )
