"""
Seeker Bot — Publisher bot commands.

Admin commands for managing channel publishing.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.common.logging import logger
from src.db.session import async_session_factory
from src.services.publisher_service import PublisherService
from src.config import settings

router = Router()


def _is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in settings.admin_ids


@router.message(Command("post"))
async def cmd_post(message: Message) -> None:
    """Queue an event for publishing. Usage: /post <event_id> [delay_minutes]"""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда только для администраторов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /post <event_id> [delay_minutes=60]")
        return

    try:
        event_id = int(parts[1])
        delay = int(parts[2]) if len(parts) > 2 else 60
    except ValueError:
        await message.answer("❌ Укажите числовой ID события и опционально задержку в минутах.")
        return

    from src.db.models.event import Event
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with async_session_factory() as session:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.cities), selectinload(Event.categories))
        )
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            await message.answer(f"❌ Событие с ID {event_id} не найдено.")
            return

        service = PublisherService(session)
        post = await service.schedule_post(event, delay_minutes=delay)
        await session.commit()

        await message.answer(
            f"✅ Событие <b>«{event.title}»</b> запланировано для публикации.\n"
            f"🆔 Пост #{post.id}\n"
            f"⏱ Через {delay} мин ({post.scheduled_at.strftime('%H:%M %d.%m')})",
        )


@router.message(Command("queue"))
async def cmd_queue(message: Message) -> None:
    """Show the publication queue."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда только для администраторов.")
        return

    async with async_session_factory() as session:
        from src.db.models.post_queue import PostQueue
        from sqlalchemy import select

        stmt = (
            select(PostQueue)
            .order_by(PostQueue.created_at.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        posts = list(result.scalars().all())

        if not posts:
            await message.answer("📭 Очередь публикаций пуста.")
            return

        lines = ["📋 <b>Последние посты в очереди:</b>\n"]
        for p in posts:
            status_emoji = {
                "pending": "⏳",
                "scheduled": "🔜",
                "published": "✅",
                "skipped": "⏭",
            }.get(p.status.value if hasattr(p.status, 'value') else p.status, "❓")
            lines.append(
                f"{status_emoji} #{p.id} | Событие #{p.event_id} | "
                f"{p.status.value if hasattr(p.status, 'value') else p.status}"
            )
            if p.scheduled_at:
                lines.append(f"   ⏱ {p.scheduled_at.strftime('%H:%M %d.%m')}")

        await message.answer("\n".join(lines))


@router.message(Command("publish_all"))
async def cmd_publish_all(message: Message) -> None:
    """Publish all scheduled posts immediately."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда только для администраторов.")
        return

    from aiogram import Bot
    bot = Bot(token=settings.bot_token)

    try:
        async with async_session_factory() as session:
            service = PublisherService(session)
            posts = await service.get_scheduled_posts()

            if not posts:
                await message.answer("📭 Нет постов, ожидающих публикации.")
                return

            success = 0
            for post in posts:
                from src.db.models.event import Event
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                stmt = (
                    select(Event)
                    .where(Event.id == post.event_id)
                    .options(selectinload(Event.cities), selectinload(Event.categories))
                )
                result = await session.execute(stmt)
                post.event = result.scalar_one_or_none()

                if post.event:
                    ok = await service.publish_post(post, bot)
                    if ok:
                        success += 1

            await session.commit()
            await message.answer(f"✅ Опубликовано {success}/{len(posts)} постов.")
    finally:
        await bot.session.close()


@router.message(Command("candidates"))
async def cmd_candidates(message: Message) -> None:
    """Show events ready for publication."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда только для администраторов.")
        return

    async with async_session_factory() as session:
        service = PublisherService(session)
        candidates = await service.get_candidates(limit=10)

        if not candidates:
            await message.answer("📭 Нет событий, готовых к публикации.")
            return

        lines = ["📰 <b>Кандидаты на публикацию:</b>\n"]
        for e in candidates:
            lines.append(f"#{e.id} {e.title[:50]}")
            if e.venue_name:
                lines.append(f"   📍 {e.venue_name}")

        kb = InlineKeyboardBuilder()
        for e in candidates[:5]:
            kb.button(text=f"📨 #{e.id}", callback_data=f"pub_queue:{e.id}")
        kb.adjust(5)

        await message.answer(
            "\n".join(lines),
            reply_markup=kb.as_markup(),
        )


@router.callback_query(F.data.startswith("pub_queue:"))
async def callback_queue_event(callback: CallbackQuery) -> None:
    """Inline button callback to queue an event for publishing."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов", show_alert=True)
        return

    event_id = int(callback.data.split(":")[1])

    from src.db.models.event import Event
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with async_session_factory() as session:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.cities), selectinload(Event.categories))
        )
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            await callback.answer("❌ Событие не найдено", show_alert=True)
            return

        service = PublisherService(session)
        await service.schedule_post(event)
        await session.commit()

        await callback.answer(f"✅ Событие «{event.title[:30]}…» запланировано!", show_alert=True)
