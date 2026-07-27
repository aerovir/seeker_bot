"""
Seeker Bot — Event API endpoints (public).

Provides endpoints for browsing events without authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.db.models.event import Event, EventCityAssignment, EventCategoryAssignment
from src.db.models.city import City
from src.db.models.category import Category
from src.api.schemas import (
    EventOut,
    EventDetailOut,
    FeedResponse,
    CityOut,
    CategoryOut,
)
from src.common.constants import EventStatus, DEFAULT_PAGE_SIZE

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.get("/events", response_model=FeedResponse)
async def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=100),
    city_id: int | None = None,
    category_id: int | None = None,
    event_type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List published events with optional filters."""
    base_query = select(Event).where(
        Event.status == EventStatus.PUBLISHED,
        or_(
            Event.start_date >= func.now(),
            Event.end_date >= func.now(),
            Event.end_date.is_(None),
        ),
    )

    if city_id:
        city_subq = (
            select(EventCityAssignment.event_id)
            .where(EventCityAssignment.city_id == city_id)
            .scalar_subquery()
        )
        base_query = base_query.where(Event.id.in_(city_subq))

    if category_id:
        cat_subq = (
            select(EventCategoryAssignment.event_id)
            .where(EventCategoryAssignment.category_id == category_id)
            .scalar_subquery()
        )
        base_query = base_query.where(Event.id.in_(cat_subq))

    if event_type:
        base_query = base_query.where(Event.event_type == event_type)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        base_query
        .order_by(Event.is_featured.desc(), Event.start_date.asc().nulls_last(), Event.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    events = list(result.scalars().all())

    items = [_event_to_out(e) for e in events]
    total_pages = max(0, (total - 1) // page_size) + 1 if total > 0 else 0

    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/events/{event_id}", response_model=EventDetailOut)
async def get_event(event_id: int, session: AsyncSession = Depends(get_session)):
    """Get event details by ID."""
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    out = EventDetailOut.model_validate(event)

    # Attach city and category names
    if event.cities:
        for assignment in event.cities:
            if assignment.city:
                out.city_names.append(assignment.city.name_ru)

    if event.categories:
        for assignment in event.categories:
            if assignment.category:
                out.category_names.append(
                    f"{assignment.category.emoji or ''} {assignment.category.name_ru}".strip()
                )

    return out


@router.get("/feed", response_model=FeedResponse)
async def public_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get public feed of all published events (no auth required)."""
    return await list_events(page=page, page_size=page_size, session=session)


@router.get("/cities", response_model=list[CityOut])
async def list_cities(session: AsyncSession = Depends(get_session)):
    """List all active cities."""
    stmt = select(City).where(City.is_active == True).order_by(City.sort_order)  # noqa: E712
    result = await session.execute(stmt)
    return [CityOut.model_validate(c) for c in result.scalars().all()]


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(session: AsyncSession = Depends(get_session)):
    """List all active categories."""
    stmt = select(Category).where(Category.is_active == True).order_by(Category.sort_order)  # noqa: E712
    result = await session.execute(stmt)
    return [CategoryOut.model_validate(c) for c in result.scalars().all()]


def _event_to_out(event: Event) -> EventOut:
    """Convert Event ORM to EventOut schema with city/category names."""
    out = EventOut.model_validate(event)

    if event.cities:
        for assignment in event.cities:
            if assignment.city:
                out.city_names.append(assignment.city.name_ru)

    if event.categories:
        for assignment in event.categories:
            if assignment.category:
                name = f"{assignment.category.emoji or ''} {assignment.category.name_ru}".strip()
                out.category_names.append(name)

    return out
