"""
Seeker Bot — Celery tasks for maintenance/cleanup.

Placeholder tasks — will be implemented in Phase 5.
"""

from celery_app.celery import celery_app
from src.common.logging import logger


@celery_app.task(queue="maintenance")
def cleanup_old_events():
    """Archive events older than 90 days."""
    logger.info("cleanup_placeholder")
    # TODO: implement in Phase 5
