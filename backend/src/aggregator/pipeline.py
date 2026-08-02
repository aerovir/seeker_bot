"""
Seeker Bot — Aggregation pipeline orchestrator.

Coordinates: Fetch → Parse → Classify → Dedup → Enrich → Store
"""

from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from src.aggregator.fetchers.rss_fetcher import RSSFetcher
from src.aggregator.parsers.rss_parser import RSSParser
from src.aggregator.classifiers.category_classifier import CategoryClassifier
from src.aggregator.classifiers.city_classifier import CityClassifier
from src.aggregator.deduplicator import Deduplicator
from src.aggregator.enricher import Enricher
from src.services.event_service import EventService
from src.common.logging import logger
from src.common.exceptions import FetchError, ParseError


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    skipped: bool = False
    reason: str | None = None
    created: list = field(default_factory=list)
    error: Exception | None = None


class AggregationPipeline:
    """Orchestrates the full content aggregation pipeline for one source."""

    def __init__(self, session: AsyncSession, source):
        self.session = session
        self.source = source

    async def execute(self, commit: bool = True) -> PipelineResult:
        """Execute the full pipeline for the configured source.

        Args:
            commit: Whether to commit the session at the end.
                Pass False for a dry-run (no writes persisted).
        """
        logger.info("pipeline_start", source=self.source.slug)

        try:
            # 1. Fetch
            raw_data = await self._fetch()
            if not raw_data:
                return PipelineResult(skipped=True, reason="empty_fetch")

            # 2. Parse
            raw_events = await self._parse(raw_data)

            # 3. Classify
            raw_events = await self._classify(raw_events)

            # 4. Dedup
            raw_events = await self._dedup(raw_events)

            if not raw_events:
                logger.info("pipeline_no_new_events", source=self.source.slug)
                return PipelineResult(created=[])

            # 5. Enrich
            enriched_events = await self._enrich(raw_events)

            # 6. Store
            created = await self._store(enriched_events)

            if commit:
                await self.session.commit()
            logger.info(
                "pipeline_complete",
                source=self.source.slug,
                created=len(created),
                committed=commit,
            )
            return PipelineResult(created=created)

        except (FetchError, ParseError) as e:
            logger.error("pipeline_error", source=self.source.slug, error=str(e))
            return PipelineResult(error=e)
        except Exception as e:
            logger.error("pipeline_unexpected_error", source=self.source.slug, error=str(e))
            await self.session.rollback()
            return PipelineResult(error=e)

    async def _fetch(self) -> bytes | None:
        """Fetch raw data from the source."""
        fetcher = RSSFetcher()
        return await fetcher.fetch(self.source)

    async def _parse(self, raw_data: bytes) -> list:
        """Parse raw data into RawEvent objects."""
        parser = RSSParser()
        return await parser.parse(raw_data, self.source)

    async def _classify(self, events: list) -> list:
        """Classify events by category and city."""
        if not events:
            return events

        cat_classifier = CategoryClassifier(self.session)
        await cat_classifier.load_categories()

        city_classifier = CityClassifier(self.session)
        await city_classifier.build_index()

        for event in events:
            event.categories = cat_classifier.classify(event.title, event.description)
            event.cities = city_classifier.extract(
                event.title, event.description,
                default_city_id=getattr(self.source, "default_city_id", None),
            )

        return events

    async def _dedup(self, events: list) -> list:
        """Filter out already-processed events."""
        dedup = Deduplicator(self.session)
        await dedup.build_index(self.source.slug, self.source.id)
        return await dedup.filter_new(events)

    async def _enrich(self, events: list) -> list:
        """Enrich events with tickets, prices, images."""
        enricher = Enricher(self.session)
        return await enricher.enrich_all(events)

    async def _store(self, events: list) -> list:
        """Store enriched events in the database."""
        service = EventService(self.session)
        created = []
        for event in events:
            db_event = await service.create_from_raw(event, self.source)
            created.append(db_event)
        return created
