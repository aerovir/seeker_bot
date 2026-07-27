"""
Seeker Bot — Admin commands: /logs, /stats, /sources, /broadcast.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import settings
from src.common.logging import logger, read_recent_logs, count_errors_last_hour

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("logs"))
async def cmd_logs(message: Message) -> None:
    """Показать последние строки лога. Использование: /logs [lines=50] [level]

    Примеры:
        /logs          — последние 50 строк
        /logs 100      — последние 100 строк
        /logs 50 ERROR — последние 50 ERROR-записей
        /logs 20 WARNING
    """
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Только для администраторов.")
        return

    parts = message.text.split()
    lines = 50
    level = None

    if len(parts) >= 2:
        try:
            lines = int(parts[1])
            lines = min(max(lines, 5), 200)  # 5-200 строк
        except ValueError:
            level = parts[1].upper()

    if len(parts) >= 3:
        level = parts[2].upper()

    await message.answer(f"🔍 Читаю лог ({lines} строк, уровень: {level or 'все'})…")

    log_text = read_recent_logs(lines=lines, level=level)

    if len(log_text) > 3800:
        log_text = log_text[:3800] + "\n\n… (обрезано, запросите меньше строк)"

    await message.answer(f"<code>{log_text}</code>")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Показать базовую статистику системы."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Только для администраторов.")
        return

    from src.db.session import async_session_factory
    from sqlalchemy import select, func
    from src.db.models.user import User
    from src.db.models.event import Event
    from src.db.models.source import ContentSource
    from src.db.models.post_queue import PostQueue, PostStatus

    async with async_session_factory() as session:
        users_total = await session.scalar(select(func.count(User.id)))
        events_total = await session.scalar(select(func.count(Event.id)))
        events_published = await session.scalar(
            select(func.count(Event.id)).where(Event.status == "published")
        )
        sources_total = await session.scalar(select(func.count(ContentSource.id)))
        sources_active = await session.scalar(
            select(func.count(ContentSource.id)).where(ContentSource.status == "active")
        )
        queue_pending = await session.scalar(
            select(func.count(PostQueue.id)).where(PostQueue.status == PostStatus.PENDING)
        )
        queue_scheduled = await session.scalar(
            select(func.count(PostQueue.id)).where(PostQueue.status == PostStatus.SCHEDULED)
        )

    errors = count_errors_last_hour()
    error_note = f"⚠️ {errors}" if errors > 0 else "✅ 0"

    text = (
        f"📊 <b>Статистика Seeker Bot</b>\n\n"
        f"👤 Пользователей: {users_total or 0}\n"
        f"📰 Событий всего: {events_total or 0}\n"
        f"✅ Опубликовано: {events_published or 0}\n"
        f"📡 Источников: {sources_total or 0} (активно: {sources_active or 0})\n"
        f"📋 Очередь: {queue_pending or 0} ожидает, {queue_scheduled or 0} запланировано\n"
        f"🚨 Ошибок за час: {error_note}\n"
    )

    await message.answer(text)


@router.message(Command("sources"))
async def cmd_sources(message: Message) -> None:
    """Показать статус всех источников."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Только для администраторов.")
        return

    from src.db.session import async_session_factory
    from sqlalchemy import select
    from src.db.models.source import ContentSource

    async with async_session_factory() as session:
        result = await session.execute(
            select(ContentSource).order_by(ContentSource.priority.desc())
        )
        sources = result.scalars().all()

    if not sources:
        await message.answer("📭 Нет источников.")
        return

    status_emoji = {"active": "✅", "paused": "⏸", "error": "❌", "disabled": "⛔"}

    lines = ["📡 <b>Источники:</b>\n"]
    for s in sources:
        emoji = status_emoji.get(s.status.value if hasattr(s.status, "value") else s.status, "❓")
        errors = f" (ошибок: {s.consecutive_errors})" if s.consecutive_errors > 0 else ""
        lines.append(f"{emoji} <b>{s.name}</b>")
        lines.append(f"   {s.feed_url[:80]}{errors}")

    await message.answer("\n".join(lines[:50]))  # Не больше 50 строк в сообщении
