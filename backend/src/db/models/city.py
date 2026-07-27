"""
Seeker Bot — City model.
"""

from sqlalchemy import String, Float, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    name_ru_prepositional: Mapped[str] = mapped_column(String(128), default="")
    name_ru_genitive: Mapped[str] = mapped_column(String(128), default="")

    region: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(64), default="Россия")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(default=0)
