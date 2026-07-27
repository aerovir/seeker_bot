"""
Seeker Bot — Notification service.

Sends digests and breaking news notifications to users.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User, NotificationFrequency
from src.db.models.event import Event, EventCityAssignment, EventCategoryAssignment
from src.db.models.notification import NotificationLog
from src.common.constants import EventStatus, NotificationType
from src.common.logging import logger


class NotificationService:
    """Business logic for user notifications."""

    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot

    async def get_digest_events(
        self,
        user: User,
        days: int = 1,
        max_events: int = 20,
    ) -> list[Event]:
        """Get events since last digest for a user.

        Args:
            user: User with preferences.
            days: Lookback period in days (used if last_digest_at is None).
            max_events: Maximum events to return.

        Returns:
            List of Event objects.
        """
        since = user.last_digest_at or (datetime.now(timezone.utc) - timedelta(days=days))

        city_ids = [p.city_id for p in user.city_preferences if p.is_active]
        category_ids = [p.category_id for p in user.category_preferences if p.is_active]

        query = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.created_at >= since,
        )

        # Apply city filter
        if city_ids:
            city_subq = (
                select(EventCityAssignment.event_id)
                .where(EventCityAssignment.city_id.in_(city_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(city_subq))

        # Apply category filter
        if category_ids:
            cat_subq = (
                select(EventCategoryAssignment.event_id)
                .where(EventCategoryAssignment.category_id.in_(category_ids))
                .scalar_subquery()
            )
            query = query.where(Event.id.in_(cat_subq))

        query = query.order_by(Event.created_at.desc()).limit(max_events)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def send_digest(self, user: User, events: list[Event]) -> bool:
        """Send a digest of events to a user.

        Args:
            user: Target user.
            events: Events to include in the digest.

        Returns:
            True if sent, False if skipped (no events or error).
        """
        if not events or not self.bot:
            return False

        text = self.build_digest_message(events)
        if not text:
            return False

        try:
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            # Update last_digest_at
            user.last_digest_at = datetime.now(timezone.utc)

            # Log notification
            await self.log_notification(
                user_id=user.id,
                notification_type=NotificationType.DIGEST,
                title=f"Дайджест: {len(events)} событий",
                was_delivered=True,
            )

            await self.session.flush()
            logger.info("digest_sent", user_id=user.id, events=len(events))
            return True

        except Exception as e:
            logger.error("digest_send_error", user_id=user.id, error=str(e))
            await self.log_notification(
                user_id=user.id,
                notification_type=NotificationType.DIGEST,
                title="Дайджест (ошибка)",
                was_delivered=False,
                error_message=str(e),
            )
            return False

    async def send_breaking_news(
        self,
        telegram_id: int,
        event,
    ) -> bool:
        """Send a breaking news notification about a single event.

        Args:
            telegram_id: User's Telegram ID.
            event: Event to notify about.

        Returns:
            True if sent successfully.
        """
        if not self.bot:
            return False

        from src.services.publisher_service import PublisherService

        text, markup = PublisherService.build_channel_message(event)

        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=f"🔔 <b>Новое событие</b>\n\n{text}",
                parse_mode="HTML",
                reply_markup=markup,
                disable_web_page_preview=False,
            )

            logger.info("breaking_news_sent", user_id=telegram_id, event_id=event.id)
            return True

        except Exception as e:
            logger.error("breaking_news_error", user_id=telegram_id, error=str(e))
            return False

    async def send_mass_notification(
        self,
        event,
        frequency_filter: NotificationFrequency | None = None,
    ) -> int:
        """Send a notification about an event to all relevant users.

        Args:
            event: Event to notify about.
            frequency_filter: Only notify users with this frequency.

        Returns:
            Number of users notified.
        """
        query = select(User).where(User.is_active == True)
        if frequency_filter:
            query = query.where(User.notification_frequency == frequency_filter)

        result = await self.session.execute(query)
        users = list(result.scalars().all())

        sent_count = 0
        for user in users:
            try:
                # Check user's city/category preferences against event
                if await self._event_matches_preferences(event, user):
                    ok = await self.send_breaking_news(user.telegram_id, event)
                    if ok:
                        sent_count += 1
            except Exception as e:
                logger.warning("mass_notification_error", user_id=user.id, error=str(e))
                continue

        return sent_count

    async def _event_matches_preferences(self, event, user: User) -> bool:
        """Check if an event matches a user's preferences."""
        city_ids = {p.city_id for p in user.city_preferences if p.is_active}
        category_ids = {p.category_id for p in user.category_preferences if p.is_active}

        if not city_ids and not category_ids:
            return True  # No preferences = show everything

        event_city_ids = set()
        if hasattr(event, "cities") and event.cities:
            for assignment in event.cities:
                event_city_ids.add(assignment.city_id)

        event_cat_ids = set()
        if hasattr(event, "categories") and event.categories:
            for assignment in event.categories:
                event_cat_ids.add(assignment.category_id)

        city_match = not city_ids or (city_ids & event_city_ids)
        cat_match = not category_ids or (category_ids & event_cat_ids)

        return city_match and cat_match

    def build_digest_message(self, events: list) -> str | None:
        """Build a digest message from a list of events.

        Args:
            events: List of Event or mock objects.

        Returns:
            Formatted HTML message, or None if events is empty.
        """
        if not events:
            return None

        from src.services.publisher_service import PublisherService

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%d.%m.%Y")

        lines = [
            f"📅 <b>Дайджест культурных событий</b>",
            f"<i>{date_str}</i>",
            "",
        ]

        # Group by event type
        from collections import defaultdict
        groups = defaultdict(list)
        for event in events:
            emoji = PublisherService._get_event_emoji(
                event.event_type if hasattr(event, "event_type") else ""
            )
            groups[emoji].append(event)

        for emoji, group in groups.items():
            for event in group[:10]:  # max 10 per group
                title = event.title if hasattr(event, "title") else str(event)
                title_short = title[:80] + "…" if len(title) > 80 else title
                lines.append(f"{emoji} <b>{title_short}</b>")

                if hasattr(event, "venue_name") and event.venue_name:
                    lines.append(f"   📍 {event.venue_name}")

                if hasattr(event, "start_date") and event.start_date:
                    from datetime import datetime as dt
                    if isinstance(event.start_date, dt):
                        lines.append(f"   🗓 {event.start_date.strftime('%d.%m')}")

            lines.append("")  # spacing between groups

        lines.append("🔍 Откройте Mini App для просмотра всех событий:")
        lines.append("👉 @seeker_bot")

        return "\n".join(lines)

    async def log_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        event_id: int | None = None,
        was_delivered: bool = True,
        error_message: str | None = None,
    ) -> NotificationLog:
        """Log a notification delivery attempt."""
        log = NotificationLog(
            user_id=user_id,
            event_id=event_id,
            notification_type=notification_type,
            title=title,
            was_delivered=was_delivered,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.flush()
        return log
