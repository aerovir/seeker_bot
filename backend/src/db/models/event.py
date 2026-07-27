"""
Seeker Bot — Event & Content models.
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.common.constants import EventStatus


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(256), unique=True, nullable=True)

    title: Mapped[str] = mapped_column(String(512), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(String(1024))

    url: Mapped[str | None] = mapped_column(String(2048))
    image_url: Mapped[str | None] = mapped_column(String(2048))
    image_data: Mapped[dict | None] = mapped_column(JSON)

    event_type: Mapped[str] = mapped_column(String(64), index=True)

    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_multiday: Mapped[bool] = mapped_column(Boolean, default=False)

    venue_name: Mapped[str | None] = mapped_column(String(512))
    venue_address: Mapped[str | None] = mapped_column(String(512))

    price_min: Mapped[float | None] = mapped_column(Float)
    price_max: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    ticket_url: Mapped[str | None] = mapped_column(String(2048))
    ticket_provider: Mapped[str | None] = mapped_column(String(64))

    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus), default=EventStatus.PENDING, index=True
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    source_id: Mapped[int | None] = mapped_column(ForeignKey("content_sources.id"))
    source: Mapped["ContentSource | None"] = relationship()
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    raw_data: Mapped[dict | None] = mapped_column(JSON)
    enrichment_data: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    categories: Mapped[list["EventCategoryAssignment"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    cities: Mapped[list["EventCityAssignment"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("is_multiday", False)
        kwargs.setdefault("currency", "RUB")
        kwargs.setdefault("status", EventStatus.PENDING)
        kwargs.setdefault("is_featured", False)
        super().__init__(**kwargs)


class EventCategoryAssignment(Base):
    __tablename__ = "event_category_assignments"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    method: Mapped[str] = mapped_column(String(32), default="keyword")

    event: Mapped["Event"] = relationship(back_populates="categories")
    category: Mapped["Category"] = relationship()


class EventCityAssignment(Base):
    __tablename__ = "event_city_assignments"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    method: Mapped[str] = mapped_column(String(32), default="gazetteer")

    event: Mapped["Event"] = relationship(back_populates="cities")
    city: Mapped["City"] = relationship()
