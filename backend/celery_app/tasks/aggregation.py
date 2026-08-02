"""
Seeker Bot — Celery tasks for content aggregation.

Bridges sync Celery workers with async pipeline code using asyncio.run().
"""

import asyncio

from celery_app.celery import celery_app
from src.db.session import celery_session_factory
from src.db.models.source import ContentSource
from src.common.constants import SourceStatus
from src.common.exceptions import FetchError
from src.common.logging import logger
from sqlalchemy import select


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300, queue="default")
def aggregate_source(self, source_id: int):
    """Aggregate a single content source."""
    try:
        asyncio.run(_aggregate_source_async(source_id))
    except Exception as e:
        logger.error("task_aggregate_error", source_id=source_id, error=str(e))
        raise self.retry(exc=e)


async def _aggregate_source_async(source_id: int):
    """Async implementation of source aggregation."""
    async with celery_session_factory() as session:
        source = await session.get(ContentSource, source_id)
        if not source:
            logger.warning("source_not_found", source_id=source_id)
            return

        if source.status != SourceStatus.ACTIVE:
            logger.debug("source_skipped_inactive", source=source.slug, status=source.status.value)
            return

        from src.aggregator.pipeline import AggregationPipeline

        pipeline = AggregationPipeline(session, source)
        result = await pipeline.execute()

        # Update source status
        if result.created:
            from datetime import datetime, timezone
            source.last_fetched_at = datetime.now(timezone.utc)
            source.consecutive_errors = 0
        elif result.error:
            logger.warning("source_fetch_error", source=source.slug, error=str(result.error))
            source.consecutive_errors += 1
            if source.consecutive_errors >= 5:
                source.status = SourceStatus.ERROR

        await session.commit()


async def _get_sources_by_priority(min_priority: int) -> list[ContentSource]:
    """Get active sources with at least the given priority."""
    async with celery_session_factory() as session:
        stmt = (
            select(ContentSource)
            .where(
                ContentSource.status == SourceStatus.ACTIVE,
                ContentSource.priority >= min_priority,
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


@celery_app.task(queue="high_priority")
def aggregate_high_priority_sources():
    """Aggregate high priority sources (every 15 min)."""
    sources = asyncio.run(_get_sources_by_priority(2))
    for source in sources:
        aggregate_source.delay(source.id)


@celery_app.task(queue="default")
def aggregate_normal_priority_sources():
    """Aggregate normal priority sources (every 30 min)."""
    sources = asyncio.run(_get_sources_by_priority(1))
    for source in sources:
        aggregate_source.delay(source.id)


@celery_app.task(queue="default")
def aggregate_low_priority_sources():
    """Aggregate low priority sources (every 2 hours)."""
    sources = asyncio.run(_get_sources_by_priority(0))
    for source in sources:
        aggregate_source.delay(source.id)
