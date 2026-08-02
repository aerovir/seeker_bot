"""
Seeker Bot — Event deduplication.

Uses exact external_id matching and source_items tracking to avoid
processing the same event twice.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.aggregator.models import RawEvent
from src.db.models.source import SourceItem
from src.common.logging import logger


class Deduplicator:
    """Filters out events that have already been processed."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._existing_guids: set[str] = set()

    async def build_index(self, source_slug: str, source_id: int) -> None:
        """Load existing source item GUIDs for dedup."""
        stmt = select(SourceItem.item_guid).where(
            SourceItem.source_id == source_id
        )
        result = await self.session.execute(stmt)
        self._existing_guids = {row[0] for row in result.all()}
        logger.debug(
            "dedup_index_built",
            source=source_slug,
            existing=len(self._existing_guids),
        )

    async def filter_new(self, events: list[RawEvent]) -> list[RawEvent]:
        """Filter out already-seen events based on source_item_guid.

        Args:
            events: List of RawEvent objects to check.

        Returns:
            List of RawEvent objects that are new (not yet processed).
        """
        if not events:
            return []

        # Фильтруем и против существующих в БД, и против уже отобранных
        # в текущем прогоне: в RSS-ленте бывают дубли с одинаковым guid,
        # иначе второй экземпляр упадёт на UNIQUE constraint external_id.
        new_events = []
        for e in events:
            if e.source_item_guid in self._existing_guids:
                continue
            self._existing_guids.add(e.source_item_guid)
            new_events.append(e)

        if len(new_events) < len(events):
            logger.debug(
                "dedup_filtered",
                total=len(events),
                duplicates=len(events) - len(new_events),
                new=len(new_events),
            )

        return new_events
