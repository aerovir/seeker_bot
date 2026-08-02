"""
Seeker Bot — Publisher service.

Manages the queue of events to be published to the Telegram channel.
Handles scheduling, message formatting, and publication.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.event import Event
from src.db.models.post_queue import PostQueue
from src.common.constants import EventStatus, PostStatus
from src.common.logging import logger
from src.config import settings
from src.aggregator.validators.event_validator import validate_event, html_to_text


class PublisherService:
    """Business logic for publishing events to Telegram channel."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.channel_id = settings.publisher_channel_id

    async def get_candidates(self, limit: int = 20) -> list[Event]:
        """Get published events that haven't been queued for publication.

        Args:
            limit: Max number of candidates to return.

        Returns:
            List of Event objects ready for publication queue.
        """
        # Subquery: event IDs already in post_queue
        queued_subq = (
            select(PostQueue.event_id)
            .where(PostQueue.event_id.isnot(None))
            .scalar_subquery()
        )

        stmt = (
            select(Event)
            .where(
                Event.status == EventStatus.PUBLISHED,
                Event.id.notin_(queued_subq),
            )
            # event.source — lazy relationship, нужен для валидации
            # (feed_url); без eager-load в async падает greenlet_spawn
            .options(selectinload(Event.source))
            .order_by(Event.is_featured.desc(), Event.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        events = list(result.scalars().all())

        logger.debug("publisher_candidates", count=len(events))
        return events

    async def schedule_post(
        self,
        event: Event,
        delay_minutes: int = 60,
        channel_id: str | None = None,
    ) -> PostQueue:
        """Schedule an event for publication.

        Args:
            event: Event to publish.
            delay_minutes: Delay before publication (default 60 min).
            channel_id: Target channel. Uses default if not specified.

        Returns:
            Created PostQueue entry.
        """
        scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        cid = channel_id or self.channel_id

        post = PostQueue(
            event_id=event.id,
            channel_id=cid,
            status=PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
        )
        self.session.add(post)
        await self.session.flush()

        logger.info(
            "post_scheduled",
            event_id=event.id,
            post_id=post.id,
            scheduled_at=scheduled_at.isoformat(),
        )
        return post

    async def get_scheduled_posts(self) -> list[PostQueue]:
        """Get posts that are scheduled and due for publishing.

        Returns:
            List of PostQueue entries ready to publish.
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(PostQueue)
            .where(
                PostQueue.status == PostStatus.SCHEDULED,
                PostQueue.scheduled_at <= now,
            )
            .order_by(PostQueue.scheduled_at.asc())
        )

        result = await self.session.execute(stmt)
        # Also eager-load the event
        posts = list(result.scalars().all())

        if posts:
            # Load events for each post
            event_ids = [p.event_id for p in posts]
            events_stmt = select(Event).where(Event.id.in_(event_ids))
            events_result = await self.session.execute(events_stmt)
            events = {e.id: e for e in events_result.scalars().all()}

            for post in posts:
                post.event = events.get(post.event_id)

            logger.debug(
                "publisher_scheduled_due",
                count=len(posts),
                now=now.isoformat(),
            )

        return posts

    @staticmethod
    def build_channel_message(event) -> tuple[str, dict | None]:
        """Build a Telegram channel message from an event.

        Args:
            event: Event (ORM or mock) with loaded cities, categories.

        Returns:
            Tuple of (message_text, inline_keyboard_markup_dict or None).
        """
        lines: list[str] = []

        # Title with emoji
        emoji = PublisherService._get_event_emoji(event.event_type)
        lines.append(f"{emoji} <b>{event.title}</b>")

        # Venue — название места жирным, адрес отдельной строкой
        venue_added = False
        if event.venue_name:
            lines.append("")
            lines.append(f"📍 <b>{event.venue_name}</b>")
            if event.venue_address:
                lines.append(f"   {event.venue_address}")
            venue_added = True
        elif event.venue_address:
            lines.append("")
            lines.append(f"📍 {event.venue_address}")
            venue_added = True

        # Cities
        city_names = []
        if hasattr(event, "cities") and event.cities:
            for assignment in event.cities:
                if hasattr(assignment, "city") and assignment.city:
                    city_names.append(assignment.city.name_ru)
        if city_names:
            if not venue_added:
                lines.append("")
            lines.append(f"🏛 {', '.join(city_names)}")

        # Dates
        date_str = PublisherService._format_date_range(
            event.start_date, event.end_date
        )
        if date_str:
            lines.append(f"🗓 {date_str}")

        # Price
        price_str = PublisherService._format_price(
            event.price_min, event.price_max, event.currency
        )
        if price_str:
            lines.append(f"💰 {price_str}")

        # Description
        if event.short_description:
            lines.append("")
            lines.append(event.short_description[:300])

        # Categories
        cat_names = []
        if hasattr(event, "categories") and event.categories:
            for assignment in event.categories:
                if hasattr(assignment, "category") and assignment.category:
                    cat_names.append(
                        f"{assignment.category.emoji or ''} {assignment.category.name_ru}".strip()
                    )
        if cat_names:
            lines.append("")
            lines.append("🏷 " + " · ".join(cat_names))

        # Хэштеги — город и категории (Telegram поддерживает кириллицу)
        tags = []
        for city in city_names:
            tag = PublisherService._to_hashtag(city)
            if tag:
                tags.append(tag)
        cat_tag_names = []
        if hasattr(event, "categories") and event.categories:
            for assignment in event.categories:
                if hasattr(assignment, "category") and assignment.category:
                    cat_tag_names.append(assignment.category.name_ru)
        for cat in cat_tag_names:
            tag = PublisherService._to_hashtag(cat)
            if tag:
                tags.append(tag)
        if tags:
            lines.append("")
            lines.append(" ".join(f"#{t}" for t in tags))

        text = "\n".join(lines)

        # Build inline keyboard
        kb = {"inline_keyboard": []}
        row = []

        if event.ticket_url:
            row.append({
                "text": "🎫 Купить билеты",
                "url": event.ticket_url,
            })

        if event.url:
            row.append({
                "text": "🔗 Подробнее",
                "url": event.url,
            })

        if row:
            kb["inline_keyboard"].append(row)

        return text, kb if kb["inline_keyboard"] else None

    @staticmethod
    def _to_hashtag(text: str) -> str:
        """Преобразовать строку в хэштег: #нижний_новгород, #концерты."""
        tag = "".join(
            ch if ch.isalnum() else "_" for ch in text.lower()
        ).strip("_")
        return tag if tag else ""

    async def publish_post(
        self,
        post: PostQueue,
        bot,
    ) -> bool:
        """Publish a queued post to the Telegram channel.

        Args:
            post: PostQueue entry with loaded event.
            bot: aiogram Bot instance.

        Returns:
            True if published successfully, False otherwise.
        """
        if not post.event:
            logger.warning("publisher_no_event", post_id=post.id)
            return False

        if not post.channel_id:
            logger.warning("publisher_no_channel", post_id=post.id)
            return False

        try:
            text, markup = self.build_channel_message(post.event)
            parse_mode = "HTML"

            # Send photo if available
            if post.event.image_url:
                try:
                    message = await bot.send_photo(
                        chat_id=post.channel_id,
                        photo=post.event.image_url,
                        caption=text,
                        parse_mode=parse_mode,
                        reply_markup=markup,
                    )
                except Exception:
                    # Fallback to text-only
                    message = await bot.send_message(
                        chat_id=post.channel_id,
                        text=text,
                        parse_mode=parse_mode,
                        reply_markup=markup,
                        disable_web_page_preview=False,
                    )
            else:
                message = await bot.send_message(
                    chat_id=post.channel_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=markup,
                    disable_web_page_preview=False,
                )

            # Update post status
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.now(timezone.utc)
            post.channel_message_id = message.message_id
            await self.session.flush()

            logger.info(
                "post_published",
                post_id=post.id,
                event_id=post.event_id,
                message_id=message.message_id,
            )
            return True

        except Exception as e:
            logger.error(
                "publisher_publish_error",
                post_id=post.id,
                error=str(e),
            )
            return False

    async def auto_queue_candidates(self, max_per_batch: int = 5, delay_minutes: int = 60) -> int:
        """Automatically queue candidates for publication.

        Публикуем только «живые» проверенные мероприятия:
        - полное событие (описание, фото, место/адрес, дата) → в очередь сразу
        - неполное → валидация: сверка с источниками; если найдено и живо —
          обогащаем недостающие поля и в очередь; если нет — статус REJECTED.

        Args:
            max_per_batch: Max events to queue.
            delay_minutes: Delay before each publication.

        Returns:
            Number of events queued.
        """
        candidates = await self.get_candidates(limit=max_per_batch)
        queued = 0

        for i, event in enumerate(candidates):
            if self._is_complete(event):
                await self.schedule_post(event, delay_minutes=delay_minutes + i * 15)
                queued += 1
                continue

            # Валидация неполного события
            result = await validate_event(self.session, event)
            if result.valid:
                self._enrich_event(event, result)
                await self.schedule_post(event, delay_minutes=delay_minutes + i * 15)
                queued += 1
                logger.info(
                    "event_validated",
                    event_id=event.id,
                    source=result.source,
                    title=event.title[:60],
                )
            else:
                event.status = EventStatus.REJECTED
                logger.info(
                    "event_rejected",
                    event_id=event.id,
                    title=event.title[:60],
                )

        await self.session.commit()
        return queued

    @staticmethod
    def _is_complete(event: Event) -> bool:
        """Полное ли событие — все поля для публикации без валидации."""
        return bool(
            event.description
            and event.image_url
            and event.venue_name
            and event.venue_address
            and event.start_date
        )

    @staticmethod
    def _enrich_event(event: Event, result) -> None:
        """Заполнить недостающие поля события из результата валидации."""
        if result.description and not event.description:
            event.description = result.description
        if result.short_description and not event.short_description:
            event.short_description = result.short_description
        if result.image_url and not event.image_url:
            event.image_url = result.image_url
        if result.venue_name and not event.venue_name:
            event.venue_name = result.venue_name
        if result.venue_address and not event.venue_address:
            event.venue_address = result.venue_address
        # Синхронизировать short_description из description, если пусто
        if not event.short_description and event.description:
            event.short_description = html_to_text(event.description)

    @staticmethod
    def _get_event_emoji(event_type: str) -> str:
        emojis = {
            "exhibition": "🎨",
            "theatre": "🎭",
            "cinema": "🎬",
            "museum": "🏛",
            "concert": "🎵",
            "festival": "🎪",
            "lecture": "📚",
            "kids": "🧒",
            "excursion": "🗺",
        }
        return emojis.get(event_type, "📌")

    @staticmethod
    def _format_date_range(start, end) -> str:
        if not start and not end:
            return ""
        if start and not end:
            return PublisherService._format_date(start)
        if not start and end:
            return f"до {PublisherService._format_date(end)}"
        return f"{PublisherService._format_date(start)} — {PublisherService._format_date(end)}"

    @staticmethod
    def _format_date(dt) -> str:
        if dt is None:
            return ""
        months = [
            "янв", "фев", "мар", "апр", "мая", "июн",
            "июл", "авг", "сен", "окт", "ноя", "дек",
        ]
        return f"{dt.day} {months[dt.month - 1]}"

    @staticmethod
    def _format_price(min_p: float | None, max_p: float | None, currency: str) -> str:
        symbol = "₽" if currency == "RUB" else currency
        if min_p is not None and max_p is not None and min_p != max_p:
            return f"{int(min_p)} — {int(max_p)} {symbol}"
        if min_p is not None:
            return f"от {int(min_p)} {symbol}"
        if max_p is not None:
            return f"до {int(max_p)} {symbol}"
        return ""
