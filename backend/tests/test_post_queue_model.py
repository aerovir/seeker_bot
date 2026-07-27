"""
Tests for PostQueue model — publication queue.
"""

from datetime import datetime, timezone
from src.common.constants import PostStatus


class TestPostQueueModel:
    def test_post_queue_creation(self):
        """PostQueue can be created with required fields."""
        from src.db.models.post_queue import PostQueue

        post = PostQueue(
            event_id=1,
            channel_id="@test_channel",
            status=PostStatus.PENDING,
        )
        assert post.event_id == 1
        assert post.channel_id == "@test_channel"
        assert post.status == PostStatus.PENDING
        assert post.scheduled_at is None
        assert post.published_at is None
        assert post.channel_message_id is None

    def test_post_queue_scheduled(self):
        """PostQueue can be scheduled with a timestamp."""
        from src.db.models.post_queue import PostQueue

        now = datetime.now(timezone.utc)
        post = PostQueue(
            event_id=2,
            channel_id="@test_channel",
            status=PostStatus.SCHEDULED,
            scheduled_at=now,
        )
        assert post.status == PostStatus.SCHEDULED
        assert post.scheduled_at == now

    def test_post_queue_published(self):
        """PostQueue records publication details."""
        from src.db.models.post_queue import PostQueue

        now = datetime.now(timezone.utc)
        post = PostQueue(
            event_id=3,
            channel_id="@test_channel",
            status=PostStatus.PUBLISHED,
            scheduled_at=now,
            published_at=now,
            channel_message_id=12345,
        )
        assert post.status == PostStatus.PUBLISHED
        assert post.channel_message_id == 12345
