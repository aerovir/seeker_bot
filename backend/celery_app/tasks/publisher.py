"""
Seeker Bot — Celery tasks for channel publishing.

Periodically publishes scheduled posts to the Telegram channel.
"""

import asyncio

from celery_app.celery import celery_app
from src.db.session import async_session_factory
from src.common.logging import logger
from src.services.publisher_service import PublisherService


@celery_app.task(queue="default")
def publish_scheduled_posts():
    """Publish all scheduled posts that are due."""
    try:
        asyncio.run(_publish_scheduled_posts_async())
    except Exception as e:
        logger.error("publish_task_error", error=str(e))


async def _publish_scheduled_posts_async():
    """Async implementation of scheduled post publishing."""
    from aiogram import Bot
    from src.config import settings

    async with async_session_factory() as session:
        service = PublisherService(session)
        posts = await service.get_scheduled_posts()

        if not posts:
            logger.debug("publish_no_posts_due")
            return

        bot = Bot(token=settings.bot_token)
        try:
            success_count = 0
            for post in posts:
                # Reload event for this post (since session may be different)
                from src.db.models.event import Event
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                stmt = (
                    select(Event)
                    .where(Event.id == post.event_id)
                    .options(
                        selectinload(Event.cities),
                        selectinload(Event.categories),
                    )
                )
                result = await session.execute(stmt)
                post.event = result.scalar_one_or_none()

                if post.event:
                    success = await service.publish_post(post, bot)
                    if success:
                        success_count += 1

            await session.commit()
            logger.info(
                "publish_batch_complete",
                total=len(posts),
                success=success_count,
            )

        finally:
            await bot.session.close()


@celery_app.task(queue="default")
def auto_queue_events():
    """Automatically queue new events for publication."""
    try:
        asyncio.run(_auto_queue_events_async())
    except Exception as e:
        logger.error("auto_queue_error", error=str(e))


async def _auto_queue_events_async():
    """Async implementation of auto-queue."""
    async with async_session_factory() as session:
        service = PublisherService(session)
        queued = await service.auto_queue_candidates(
            max_per_batch=5,
            delay_minutes=60,
        )
        await session.commit()

        if queued:
            logger.info("auto_queue_complete", queued=queued)
