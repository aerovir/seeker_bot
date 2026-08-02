from celery_app.celery import celery_app

# Регистрация задач в воркере: без импорта модулей celery_app.tasks.*
# воркер не знает задач и падает с KeyError при приёме из beat.
import celery_app.tasks.aggregation  # noqa: E402,F401
import celery_app.tasks.cleanup       # noqa: E402,F401
import celery_app.tasks.notification  # noqa: E402,F401
import celery_app.tasks.publisher     # noqa: E402,F401

__all__ = ["celery_app"]
