"""
Tests for Celery configuration — app creation and task registration.
"""


class TestCeleryConfig:
    def test_celery_app_import(self):
        """Celery app can be imported and has expected attributes."""
        from celery_app.celery import celery_app as app

        assert app.main == "seeker_bot"
        assert "aggregate-high-priority" in app.conf.beat_schedule
        assert "aggregate-normal-priority" in app.conf.beat_schedule
        assert "aggregate-low-priority" in app.conf.beat_schedule

    def test_celery_tasks_registered(self):
        """Celery tasks are registered correctly."""
        from celery_app.celery import celery_app as app

        # Ensure tasks module is loaded
        import celery_app.tasks.aggregation  # noqa: F401
        import celery_app.tasks.notification  # noqa: F401
        import celery_app.tasks.cleanup  # noqa: F401

        task_names = list(app.tasks.keys())
        assert any("aggregate_source" in name for name in task_names)
        assert any("send_daily_digests" in name for name in task_names)
        assert any("cleanup_old_events" in name for name in task_names)

    def test_beat_schedule_queues(self):
        """Each beat task specifies a valid queue."""
        from celery_app.celery import celery_app as app

        valid_queues = {"high_priority", "default", "notifications", "maintenance"}

        for task_name, task_config in app.conf.beat_schedule.items():
            queue = task_config.get("options", {}).get("queue", "default")
            assert queue in valid_queues, f"Task {task_name} has invalid queue: {queue}"

    def test_celery_timezone(self):
        """Celery is configured for Moscow time."""
        from celery_app.celery import celery_app as app

        assert app.conf.timezone == "Europe/Moscow"
