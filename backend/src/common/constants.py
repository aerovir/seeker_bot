"""
Seeker Bot — Constants and enums.
"""

from enum import Enum


class SourceType(str, Enum):
    RSS = "rss"
    WEB_SCRAPE = "web_scrape"
    API = "api"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class EventStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class NotificationFrequency(str, Enum):
    REALTIME = "realtime"
    DIGEST_DAILY = "daily"
    DIGEST_WEEKLY = "weekly"
    NONE = "none"


class NotificationType(str, Enum):
    DIGEST = "digest"
    BREAKING = "breaking"
    TEST = "test"


class PostStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    SKIPPED = "skipped"


# Limits
MAX_USER_CITIES = 5
MAX_USER_CATEGORIES = 10
MAX_EVENT_TITLE_LENGTH = 512
MAX_EVENT_DESCRIPTION_LENGTH = 10000
MAX_SOURCE_NAME_LENGTH = 256

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Categories
CATEGORY_EMOJIS = {
    "exhibitions": "🎨",
    "theatre": "🎭",
    "cinema": "🎬",
    "museums": "🏛",
    "concerts": "🎵",
    "festivals": "🎪",
    "lectures": "📚",
    "other": "📌",
}
