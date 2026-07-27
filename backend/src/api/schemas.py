"""
Seeker Bot — Pydantic schemas for REST API.

Request and response models for all TMA endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from src.common.constants import MAX_USER_CITIES, MAX_USER_CATEGORIES


class EventOut(BaseModel):
    """Event response model for TMA feed."""
    id: int
    title: str
    description: str | None = None
    short_description: str | None = None
    url: str | None = None
    image_url: str | None = None
    event_type: str
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
    is_featured: bool = False
    city_names: list[str] = Field(default_factory=list)
    category_names: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EventDetailOut(EventOut):
    """Detailed event response with full description."""
    raw_data: dict | None = None
    source_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PreferencesUpdate(BaseModel):
    """User preferences update request."""
    city_ids: list[int]
    category_ids: list[int]

    @field_validator("city_ids")
    @classmethod
    def check_city_ids_length(cls, v: list[int]) -> list[int]:
        if len(v) > MAX_USER_CITIES:
            raise ValueError(f"Maximum {MAX_USER_CITIES} cities allowed")
        return v

    @field_validator("category_ids")
    @classmethod
    def check_category_ids_length(cls, v: list[int]) -> list[int]:
        if len(v) > MAX_USER_CATEGORIES:
            raise ValueError(f"Maximum {MAX_USER_CATEGORIES} categories allowed")
        return v


class PreferencesOut(BaseModel):
    """User preferences response."""
    city_ids: list[int]
    city_names: list[str] = Field(default_factory=list)
    category_ids: list[int]
    category_names: list[str] = Field(default_factory=list)
    notification_frequency: str = "daily"


class FeedResponse(BaseModel):
    """Paginated feed response."""
    items: list[EventOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CityOut(BaseModel):
    """City response model."""
    id: int
    slug: str
    name_ru: str
    name_en: str | None = None
    region: str | None = None

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    """Category response model."""
    id: int
    slug: str
    name_ru: str
    name_en: str | None = None
    emoji: str | None = None

    model_config = {"from_attributes": True}


class SearchParams(BaseModel):
    """Search query parameters."""
    q: str = Field(..., min_length=1, max_length=200)
    city_id: int | None = None
    category_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
