"""
Tests for Celery configuration — app creation and task registration.
"""

import pytest


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


class TestAggregationTask:
    @pytest.mark.asyncio
    async def test_last_fetched_at_is_datetime(self):
        """On successful aggregation, last_fetched_at is a datetime, not a float."""
        from datetime import datetime
        from unittest.mock import AsyncMock, MagicMock, patch
        from celery_app.tasks import aggregation
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType, SourceStatus
        from src.aggregator.pipeline import PipelineResult

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
        )

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=source)
        mock_session.commit = AsyncMock()

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_af = MagicMock(return_value=mock_cm)
        mock_result = PipelineResult(created=[MagicMock(id=1)])

        with patch.object(aggregation, "async_session_factory", mock_af), \
             patch("src.aggregator.pipeline.AggregationPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.execute = AsyncMock(return_value=mock_result)
            mock_pipeline_cls.return_value = mock_pipeline

            await aggregation._aggregate_source_async(1)

        assert isinstance(source.last_fetched_at, datetime)
