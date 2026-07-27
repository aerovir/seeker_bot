"""
Seeker Bot — Post Queue model.

Tracks events queued for publication to the Telegram channel.
"""

from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.common.constants import PostStatus


class PostQueue(Base):
    __tablename__ = "post_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    channel_id: Mapped[str] = mapped_column(String(128), default="")

    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus), default=PostStatus.PENDING, index=True
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    event: Mapped["Event"] = relationship()
