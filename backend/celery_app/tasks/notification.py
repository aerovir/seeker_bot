"""
Seeker Bot — Celery tasks for notifications.

Sends daily and weekly digests to users.
"""

import asyncio

from celery_app.celery import celery_app
from src.db.session import async_session_factory
from src.db.models.user import User, NotificationFrequency
from src.common.logging import logger
from sqlalchemy import select


@celery_app.task(queue="notifications")
def send_daily_digests():
    """Send daily digests to users."""
    try:
        asyncio.run(_send_digests_async(NotificationFrequency.DIGEST_DAILY))
    except Exception as e:
        logger.error("digest_daily_error", error=str(e))


@celery_app.task(queue="notifications")
def send_weekly_digests():
    """Send weekly digests to users."""
    try:
        asyncio.run(_send_digests_async(NotificationFrequency.DIGEST_WEEKLY))
    except Exception as e:
        logger.error("digest_weekly_error", error=str(e))


async def _send_digests_async(frequency: NotificationFrequency):
    """Send digests to all users with the given frequency."""
    from src.config import settings
    from aiogram import Bot
    from src.services.notification_service import NotificationService

    async with async_session_factory() as session:
        # Get all users with this frequency
        stmt = select(User).where(
            User.is_active == True,
            User.notification_frequency == frequency,
        )
        result = await session.execute(stmt)
        users = list(result.scalars().all())

        if not users:
            logger.debug("digest_no_users", frequency=frequency.value)
            return

        bot = Bot(token=settings.bot_token)
        try:
            service = NotificationService(session, bot)
            sent_count = 0

            for user in users:
                events = await service.get_digest_events(user)
                if events:
                    ok = await service.send_digest(user, events)
                    if ok:
                        sent_count += 1

            await session.commit()
            logger.info(
                "digest_batch_complete",
                frequency=frequency.value,
                users=len(users),
                sent=sent_count,
            )

        finally:
            await bot.session.close()
