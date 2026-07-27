"""
Seeker Bot — User & Preferences models.
"""

from datetime import datetime

from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.common.constants import NotificationFrequency


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(128))
    first_name: Mapped[str | None] = mapped_column(String(256))
    last_name: Mapped[str | None] = mapped_column(String(256))
    language_code: Mapped[str] = mapped_column(String(8), default="ru")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    notification_frequency: Mapped[NotificationFrequency] = mapped_column(
        SAEnum(NotificationFrequency), default=NotificationFrequency.DIGEST_DAILY
    )
    last_digest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    city_preferences: Mapped[list["UserCityPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    category_preferences: Mapped[list["UserCategoryPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_admin", False)
        kwargs.setdefault("language_code", "ru")
        kwargs.setdefault("notification_frequency", NotificationFrequency.DIGEST_DAILY)
        super().__init__(**kwargs)


class UserCityPreference(Base):
    __tablename__ = "user_city_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="city_preferences")
    city: Mapped["City"] = relationship()


class UserCategoryPreference(Base):
    __tablename__ = "user_category_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="category_preferences")
    category: Mapped["Category"] = relationship()
