"""
Integration tests — services with real DB queries.

Tests: FeedService, UserService, PublisherService, EventService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from sqlalchemy import select


class TestEventServiceIntegration:
    @pytest.mark.asyncio
    async def test_create_event_with_categories(self, db_session, sample_categories):
        """EventService creates an event with category assignments."""
        from src.services.event_service import EventService
        from src.aggregator.models import EnrichedEvent
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType, SourceStatus

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
        )
        db_session.add(source)
        await db_session.flush()

        service = EventService(db_session)
        enriched = EnrichedEvent(
            title="Интеграционный тест",
            description="Описание",
            content_source_id=1,
            source_slug="test",
            source_item_guid="int-hash-1",
            categories=[(1, 0.9, "keyword")],
            cities=[],
        )

        event = await service.create_from_raw(enriched, source)
        await db_session.commit()

        assert event.id is not None
        assert event.title == "Интеграционный тест"
        assert event.external_id == "test:int-hash-1"

        # Verify category assignment was persisted
        from src.db.models.event import EventCategoryAssignment
        result = await db_session.execute(
            select(EventCategoryAssignment).where(EventCategoryAssignment.event_id == event.id)
        )
        assignments = list(result.scalars().all())
        assert len(assignments) == 1
        assert assignments[0].category_id == 1


class TestSourceItemTracking:
    """SourceItem must be created on event ingest so subsequent runs dedup."""

    @pytest.mark.asyncio
    async def test_create_event_creates_source_item(self, db_session):
        """create_from_raw persists a SourceItem for the event."""
        from src.services.event_service import EventService
        from src.aggregator.models import EnrichedEvent
        from src.db.models.source import ContentSource, SourceItem
        from src.common.constants import SourceType, SourceStatus
        from sqlalchemy import select

        source = ContentSource(
            name="Test", slug="test-source", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
        )
        db_session.add(source)
        await db_session.flush()

        enriched = EnrichedEvent(
            title="Тест SourceItem",
            description="Описание",
            content_source_id=source.id,
            source_slug="test-source",
            source_item_guid="hash-abc-123",
            categories=[],
            cities=[],
        )

        event = await EventService(db_session).create_from_raw(enriched, source)
        await db_session.commit()

        result = await db_session.execute(
            select(SourceItem).where(SourceItem.source_id == source.id)
        )
        items = list(result.scalars().all())
        assert len(items) == 1
        assert items[0].item_guid == "hash-abc-123"
        assert items[0].event_id == event.id

    @pytest.mark.asyncio
    async def test_second_pipeline_run_dedups(self, db_session):
        """After first ingest, a second run of the same item is filtered out."""
        from src.services.event_service import EventService
        from src.aggregator.models import EnrichedEvent, RawEvent
        from src.aggregator.deduplicator import Deduplicator
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType, SourceStatus

        source = ContentSource(
            name="Test", slug="test-source", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
        )
        db_session.add(source)
        await db_session.flush()

        enriched = EnrichedEvent(
            title="Событие", description="Описание",
            content_source_id=source.id, source_slug="test-source",
            source_item_guid="same-guid", categories=[], cities=[],
        )
        await EventService(db_session).create_from_raw(enriched, source)
        await db_session.commit()

        # Second run: dedup index now contains the guid
        dedup = Deduplicator(db_session)
        await dedup.build_index(source.slug, source.id)
        new_events = await dedup.filter_new([
            RawEvent(title="Событие", source_item_guid="same-guid"),
        ])
        assert new_events == []


class TestFeedServiceIntegration:
    @pytest.mark.asyncio
    async def test_feed_with_preferences(self, db_session, sample_user, sample_cities, sample_categories):
        """FeedService returns personalized feed based on DB preferences."""
        from src.services.feed_service import FeedService
        from src.db.models.event import Event
        from src.db.models.event import EventCityAssignment, EventCategoryAssignment
        from src.common.constants import EventStatus
        from src.db.models.user import UserCityPreference, UserCategoryPreference
        from sqlalchemy.orm import selectinload

        # Create a test event with city + category assignments
        event = Event(
            id=1,
            title="Тестовое событие",
            event_type="exhibition",
            status=EventStatus.PUBLISHED,
            start_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )
        db_session.add(event)
        await db_session.flush()

        # Assign to city 1 and category 1
        db_session.add(EventCityAssignment(event_id=1, city_id=1))
        db_session.add(EventCategoryAssignment(event_id=1, category_id=1))

        # Set user preferences
        db_session.add(UserCityPreference(user_id=12345, city_id=1))
        db_session.add(UserCategoryPreference(user_id=12345, category_id=1))
        await db_session.commit()

        # Reload user with preferences
        result = await db_session.execute(
            select(sample_user.__class__)
            .where(sample_user.__class__.id == 12345)
            .options(selectinload(sample_user.__class__.city_preferences),
                     selectinload(sample_user.__class__.category_preferences))
        )
        user = result.scalar_one()

        feed_service = FeedService(db_session)
        events, total = await feed_service.get_personalized_feed(user)

        assert total >= 1
        assert any(e.id == 1 for e in events)


class TestPublisherServiceIntegration:
    @pytest.mark.asyncio
    async def test_candidates_query(self, db_session):
        """PublisherService.get_candidates returns correct events."""
        from src.services.publisher_service import PublisherService
        from src.db.models.event import Event
        from src.common.constants import EventStatus

        event_published = Event(
            title="Published", event_type="concert", status=EventStatus.PUBLISHED
        )
        event_pending = Event(
            title="Pending", event_type="concert", status=EventStatus.PENDING
        )
        db_session.add(event_published)
        db_session.add(event_pending)
        await db_session.commit()

        service = PublisherService(db_session)
        candidates = await service.get_candidates(limit=10)

        assert len(candidates) == 1
        assert candidates[0].title == "Published"

    @pytest.mark.asyncio
    async def test_post_queue_flow(self, db_session):
        """PostQueue status flows through pending → scheduled → published."""
        from src.services.publisher_service import PublisherService
        from src.db.models.event import Event
        from src.db.models.post_queue import PostQueue
        from src.common.constants import EventStatus, PostStatus
        from sqlalchemy import select

        event = Event(title="Queue Test", event_type="theatre", status=EventStatus.PUBLISHED)
        db_session.add(event)
        await db_session.flush()

        service = PublisherService(db_session)
        post = await service.schedule_post(event, delay_minutes=30)
        await db_session.commit()

        assert post.status == PostStatus.SCHEDULED
        assert post.event_id == event.id

        # Mark as published
        post.status = PostStatus.PUBLISHED
        await db_session.commit()

        result = await db_session.execute(
            select(PostQueue).where(PostQueue.id == post.id)
        )
        found = result.scalar_one()
        assert found.status == PostStatus.PUBLISHED
