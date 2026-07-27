"""
Seeker Bot — Notification log model.
"""

from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.common.constants import NotificationType


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)

    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType), default=NotificationType.DIGEST
    )
    title: Mapped[str] = mapped_column(String(512))

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    was_delivered: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
