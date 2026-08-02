"""
Seeker Bot — Event service.

Business logic for creating and querying events.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.event import Event, EventCategoryAssignment, EventCityAssignment
from src.common.constants import EventStatus
from src.common.logging import logger

# Category slug -> event_type mapping
CATEGORY_TO_EVENT_TYPE = {
    "exhibitions": "exhibition",
    "theatre": "theatre",
    "cinema": "cinema",
    "museums": "museum",
    "concerts": "concert",
    "festivals": "festival",
    "lectures": "lecture",
    "kids": "kids",
    "excursions": "excursion",
    "other": "other",
}


class EventService:
    """Business logic for event management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_from_raw(self, enriched_event, source) -> Event:
        """Create an Event DB record from an EnrichedEvent.

        Args:
            enriched_event: EnrichedEvent with all data.
            source: ContentSource the event came from.

        Returns:
            The created Event DB model instance.
        """
        # Map category slugs to event_type
        category_slug_map: dict[int, str] = {}
        if enriched_event.categories:
            from src.db.models.category import Category

            cat_ids = [c[0] for c in enriched_event.categories]
            stmt = select(Category).where(Category.id.in_(cat_ids))
            result = await self.session.execute(stmt)
            for cat in result.scalars().all():
                category_slug_map[cat.id] = cat.slug

        event_type = self._detect_event_type(
            enriched_event.categories, category_slug_map
        )

        external_id = f"{source.slug}:{enriched_event.source_item_guid}"

        event = Event(
            external_id=external_id,
            title=enriched_event.title,
            description=enriched_event.description,
            short_description=enriched_event.short_description,
            url=enriched_event.url,
            image_url=enriched_event.image_url,
            event_type=event_type,
            start_date=enriched_event.start_date,
            end_date=enriched_event.end_date,
            is_multiday=enriched_event.is_multiday,
            venue_name=enriched_event.venue_name,
            venue_address=enriched_event.venue_address,
            price_min=enriched_event.price_min,
            price_max=enriched_event.price_max,
            currency=enriched_event.currency,
            ticket_url=enriched_event.ticket_url,
            ticket_provider=enriched_event.ticket_provider,
            status=EventStatus.PUBLISHED,
            source_id=source.id,
            source_url=source.feed_url,
        )
        self.session.add(event)
        await self.session.flush()

        # Track the source item so subsequent pipeline runs can dedup on it
        from src.db.models.source import SourceItem

        source_item = SourceItem(
            source_id=source.id,
            item_guid=enriched_event.source_item_guid,
            item_hash=enriched_event.source_item_guid,
            event_id=event.id,
        )
        self.session.add(source_item)

        # Create category assignments
        for cat_id, confidence, method in enriched_event.categories:
            assignment = EventCategoryAssignment(
                event_id=event.id,
                category_id=cat_id,
                confidence=confidence,
                method=method,
            )
            self.session.add(assignment)

        # Create city assignments
        for city_id, confidence, method in enriched_event.cities:
            assignment = EventCityAssignment(
                event_id=event.id,
                city_id=city_id,
                confidence=confidence,
                method=method,
            )
            self.session.add(assignment)

        logger.debug("event_created", event_id=event.id, external_id=external_id)
        return event

    @staticmethod
    def _detect_event_type(
        categories: list[tuple[int, float, str]],
        category_slug_map: dict[int, str],
    ) -> str:
        """Detect event_type from classified categories."""
        if not categories:
            return "other"

        top_cat_id = categories[0][0]
        slug = category_slug_map.get(top_cat_id, "")
        return CATEGORY_TO_EVENT_TYPE.get(slug, "other")
