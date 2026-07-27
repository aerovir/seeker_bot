"""
Seeker Bot — Aggregator data models.

RawEvent: result of parsing a source item before classification/enrichment.
EnrichedEvent: RawEvent with added ticket/price/image data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SourceRef:
    """Reference to the source of an event."""
    source_id: int
    source_slug: str
    url: str | None = None


@dataclass
class RawEvent:
    """Raw event extracted from a content source (before enrichment)."""
    title: str
    description: str | None = None
    content_source_id: int = 0
    source_slug: str = ""
    source_item_guid: str = ""
    source_url: str | None = None

    url: str | None = None
    image_url: str | None = None

    start_date: datetime | None = None
    end_date: datetime | None = None
    is_multiday: bool = False

    venue_name: str | None = None
    venue_address: str | None = None

    price_text: str | None = None

    categories: list[tuple[int, float, str]] = field(default_factory=list)
    cities: list[tuple[int, float, str]] = field(default_factory=list)


@dataclass
class EnrichedEvent:
    """Event enriched with ticket/price/image data."""
    title: str
    description: str | None = None
    short_description: str | None = None
    content_source_id: int = 0
    source_slug: str = ""
    source_item_guid: str = ""
    source_url: str | None = None

    url: str | None = None
    image_url: str | None = None

    start_date: datetime | None = None
    end_date: datetime | None = None
    is_multiday: bool = False

    venue_name: str | None = None
    venue_address: str | None = None

    price_min: float | None = None
    price_max: float | None = None
    currency: str = "RUB"
    ticket_url: str | None = None
    ticket_provider: str | None = None

    categories: list[tuple[int, float, str]] = field(default_factory=list)
    cities: list[tuple[int, float, str]] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: RawEvent) -> "EnrichedEvent":
        return cls(
            title=raw.title,
            description=raw.description,
            content_source_id=raw.content_source_id,
            source_slug=raw.source_slug,
            source_item_guid=raw.source_item_guid,
            source_url=raw.source_url,
            url=raw.url,
            image_url=raw.image_url,
            start_date=raw.start_date,
            end_date=raw.end_date,
            is_multiday=raw.is_multiday,
            venue_name=raw.venue_name,
            venue_address=raw.venue_address,
            categories=raw.categories,
            cities=raw.cities,
        )
