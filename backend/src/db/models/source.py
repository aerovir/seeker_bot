"""
Seeker Bot — Content Source and SourceItem models.
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Boolean, ForeignKey, JSON, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.common.constants import SourceType, SourceStatus


class ContentSource(Base):
    __tablename__ = "content_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    feed_url: Mapped[str] = mapped_column(String(2048))
    base_url: Mapped[str | None] = mapped_column(String(2048))

    config: Mapped[dict] = mapped_column(JSON, default=dict)

    fetch_interval_minutes: Mapped[int] = mapped_column(default=30)
    retry_count: Mapped[int] = mapped_column(default=3)
    timeout_seconds: Mapped[int] = mapped_column(default=30)

    default_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"))

    status: Mapped[SourceStatus] = mapped_column(
        SAEnum(SourceStatus), default=SourceStatus.ACTIVE, index=True
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    consecutive_errors: Mapped[int] = mapped_column(default=0)

    priority: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    default_city: Mapped["City | None"] = relationship()
    default_categories: Mapped[list["Category"]] = relationship(
        secondary="source_default_categories"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("config", {})
        kwargs.setdefault("status", SourceStatus.ACTIVE)
        kwargs.setdefault("fetch_interval_minutes", 30)
        kwargs.setdefault("retry_count", 3)
        kwargs.setdefault("timeout_seconds", 30)
        kwargs.setdefault("consecutive_errors", 0)
        kwargs.setdefault("priority", 0)
        super().__init__(**kwargs)


class SourceDefaultCategory(Base):
    """Many-to-many between ContentSource and Category."""

    __tablename__ = "source_default_categories"

    source_id: Mapped[int] = mapped_column(
        ForeignKey("content_sources.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )


class SourceItem(Base):
    """Tracks items already fetched from a source (for dedup)."""

    __tablename__ = "source_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("content_sources.id", ondelete="CASCADE"), index=True
    )
    item_guid: Mapped[str] = mapped_column(String(512))
    item_hash: Mapped[str] = mapped_column(String(64))

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("source_id", "item_guid", name="uq_source_item"),
    )
