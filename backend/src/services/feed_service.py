"""
Seeker Bot — Feed service.

Generates personalized event feeds based on user preferences.
"""

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.event import Event, EventCityAssignment, EventCategoryAssignment
from src.db.models.user import User
from src.common.constants import EventStatus, DEFAULT_PAGE_SIZE
from src.common.logging import logger


class FeedService:
    """Business logic for personalized event feed generation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_personalized_feed(
        self,
        user: User,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[Event], int]:
        """Build a personalized event feed for a user.

        Filters by:
        1. User's selected cities (OR)
        2. User's selected categories (OR)
        3. Events with start_date >= now or end_date >= now
        4. Status = PUBLISHED

        Args:
            user: User with city_preferences and category_preferences loaded.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (list of Event objects, total count).
        """
        city_ids = [p.city_id for p in user.city_preferences if p.is_active]
        category_ids = [p.category_id for p in user.category_preferences if p.is_active]

        # Base query: published events that haven't ended
        base_query = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            or_(
                Event.start_date >= func.now(),
                Event.end_date >= func.now(),
                Event.end_date.is_(None),
            ),
        )

        # Apply city filter
        if city_ids:
            city_subq = (
                select(EventCityAssignment.event_id)
                .where(EventCityAssignment.city_id.in_(city_ids))
                .scalar_subquery()
            )
            base_query = base_query.where(Event.id.in_(city_subq))

        # Apply category filter
        if category_ids:
            cat_subq = (
                select(EventCategoryAssignment.event_id)
                .where(EventCategoryAssignment.category_id.in_(category_ids))
                .scalar_subquery()
            )
            base_query = base_query.where(Event.id.in_(cat_subq))

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = (
            base_query
            .order_by(Event.is_featured.desc(), Event.start_date.asc().nulls_last(), Event.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        events = list(result.scalars().all())

        logger.debug(
            "feed_generated",
            user_id=user.id,
            cities=city_ids,
            categories=category_ids,
            total=total,
            page=page,
            returned=len(events),
        )

        return events, total

    async def get_upcoming_events(
        self,
        user: User,
        limit: int = 5,
    ) -> list[Event]:
        """Get upcoming events for the user (next 7 days)."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        week_later = now + timedelta(days=7)

        city_ids = [p.city_id for p in user.city_preferences if p.is_active]
        category_ids = [p.category_id for p in user.category_preferences if p.is_active]

        query = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.start_date >= now,
            Event.start_date <= week_later,
        )

        if city_ids:
            city_subq = (
                select(EventCityAssignment.event_id)
                .where(EventCityAssignment.city_id.in_(city_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(city_subq))

        if category_ids:
            cat_subq = (
                select(EventCategoryAssignment.event_id)
                .where(EventCategoryAssignment.category_id.in_(category_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(cat_subq))

        query = query.order_by(Event.start_date.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_today_events(self, user: User) -> list[Event]:
        """Get events happening today."""
        from datetime import datetime, timezone

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)

        city_ids = [p.city_id for p in user.city_preferences if p.is_active]
        category_ids = [p.category_id for p in user.category_preferences if p.is_active]

        query = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            or_(
                Event.start_date.between(today_start, today_end),
                Event.end_date.between(today_start, today_end),
                Event.start_date <= today_start,
                Event.end_date >= today_end,
            ),
        )

        if city_ids:
            city_subq = (
                select(EventCityAssignment.event_id)
                .where(EventCityAssignment.city_id.in_(city_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(city_subq))

        if category_ids:
            cat_subq = (
                select(EventCategoryAssignment.event_id)
                .where(EventCategoryAssignment.category_id.in_(category_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(cat_subq))

        query = query.order_by(Event.start_date.asc()).limit(50)
        result = await self.session.execute(query)
        return list(result.scalars().all())
