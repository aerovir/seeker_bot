"""
Seeker Bot — Celery application configuration.

Defines the Celery app with Redis broker and beat schedule
for periodic content aggregation.
"""

from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery(
    "seeker_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_max_tasks_per_child=100,
    worker_concurrency=4,
)

# Beat schedule
celery_app.conf.beat_schedule = {
    "aggregate-high-priority": {
        "task": "celery_app.tasks.aggregation.aggregate_high_priority_sources",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "high_priority"},
    },
    "aggregate-normal-priority": {
        "task": "celery_app.tasks.aggregation.aggregate_normal_priority_sources",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "default"},
    },
    "aggregate-low-priority": {
        "task": "celery_app.tasks.aggregation.aggregate_low_priority_sources",
        "schedule": crontab(hour="*/2"),
        "options": {"queue": "default"},
    },
    "send-daily-digests": {
        "task": "celery_app.tasks.notification.send_daily_digests",
        "schedule": crontab(hour="9", minute="0"),
        "options": {"queue": "notifications"},
    },
    "send-weekly-digests": {
        "task": "celery_app.tasks.notification.send_weekly_digests",
        "schedule": crontab(hour="9", minute="0", day_of_week="monday"),
        "options": {"queue": "notifications"},
    },
    "cleanup-old-events": {
        "task": "celery_app.tasks.cleanup.cleanup_old_events",
        "schedule": crontab(hour="3", minute="0"),
        "options": {"queue": "maintenance"},
    },
}
