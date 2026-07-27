"""
Seeker Bot — Celery tasks for notifications.

Placeholder tasks — will be implemented in Phase 4.
"""

from celery_app.celery import celery_app
from src.common.logging import logger


@celery_app.task(queue="notifications")
def send_daily_digests():
    """Send daily digests to users."""
    logger.info("digest_daily_placeholder")
    # TODO: implement in Phase 4


@celery_app.task(queue="notifications")
def send_weekly_digests():
    """Send weekly digests to users."""
    logger.info("digest_weekly_placeholder")
    # TODO: implement in Phase 4
