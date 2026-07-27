"""
Tests for constants and enums.
"""

from src.common.constants import (
    SourceType, SourceStatus, EventStatus,
    NotificationFrequency, NotificationType,
    CATEGORY_EMOJIS, MAX_USER_CITIES, DEFAULT_PAGE_SIZE,
)


class TestEnums:
    def test_source_type_values(self):
        assert SourceType.RSS.value == "rss"
        assert SourceType.WEB_SCRAPE.value == "web_scrape"
        assert SourceType.API.value == "api"

    def test_event_status_values(self):
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.PUBLISHED.value == "published"
        assert EventStatus.ARCHIVED.value == "archived"
        assert EventStatus.REJECTED.value == "rejected"

    def test_notification_frequency_values(self):
        assert NotificationFrequency.REALTIME.value == "realtime"
        assert NotificationFrequency.DIGEST_DAILY.value == "daily"
        assert NotificationFrequency.DIGEST_WEEKLY.value == "weekly"
        assert NotificationFrequency.NONE.value == "none"


class TestConstants:
    def test_category_emojis(self):
        assert CATEGORY_EMOJIS["exhibitions"] == "🎨"
        assert CATEGORY_EMOJIS["theatre"] == "🎭"
        assert CATEGORY_EMOJIS["cinema"] == "🎬"

    def test_limits(self):
        assert MAX_USER_CITIES == 5
        assert DEFAULT_PAGE_SIZE == 20
