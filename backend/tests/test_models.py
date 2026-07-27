"""
Tests for SQLAlchemy models — construction and relationships.
"""

import pytest
from datetime import datetime

from src.common.constants import (
    NotificationFrequency,
    EventStatus,
    SourceType,
    SourceStatus,
)
from src.db.models.user import User, UserCityPreference, UserCategoryPreference
from src.db.models.event import Event, EventCategoryAssignment, EventCityAssignment
from src.db.models.source import ContentSource, SourceItem, SourceDefaultCategory
from src.db.models.category import Category
from src.db.models.city import City
from src.db.models.notification import NotificationLog


class TestUserModel:
    def test_user_minimal_creation(self):
        """User can be created with minimal fields."""
        user = User(id=123, telegram_id=123)
        assert user.id == 123
        assert user.telegram_id == 123
        assert user.is_active is True
        assert user.is_admin is False
        assert user.notification_frequency == NotificationFrequency.DIGEST_DAILY
        assert user.language_code == "ru"

    def test_user_full_creation(self):
        """User can be created with all fields."""
        now = datetime.utcnow()
        user = User(
            id=456,
            telegram_id=456,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="en",
            is_active=True,
            is_admin=True,
            notification_frequency=NotificationFrequency.REALTIME,
        )
        assert user.username == "testuser"
        assert user.is_admin is True
        assert user.notification_frequency == NotificationFrequency.REALTIME


class TestEventModel:
    def test_event_minimal_creation(self):
        """Event can be created with required fields only."""
        event = Event(title="Test Event", event_type="exhibition")
        assert event.title == "Test Event"
        assert event.event_type == "exhibition"
        assert event.status == EventStatus.PENDING
        assert event.currency == "RUB"
        assert event.is_multiday is False

    def test_event_with_full_data(self):
        """Event can be created with full data."""
        event = Event(
            title="Большая выставка",
            description="Описание выставки",
            short_description="Кратко",
            event_type="exhibition",
            venue_name="Третьяковская галерея",
            venue_address="Лаврушинский пер., 10",
            price_min=400.0,
            price_max=800.0,
            ticket_url="https://example.com/tickets",
            ticket_provider="yandex_afisha",
            status=EventStatus.PUBLISHED,
            is_featured=True,
        )
        assert event.venue_name == "Третьяковская галерея"
        assert event.price_min == 400.0
        assert event.status == EventStatus.PUBLISHED
        assert event.is_featured is True

    def test_event_category_assignment(self):
        """Event can be linked to categories."""
        event = Event(title="Test", event_type="concert")
        cat = Category(slug="concerts", name_ru="Концерты", name_en="Concerts")
        assignment = EventCategoryAssignment(
            event=event, category=cat, confidence=0.95, method="keyword"
        )
        assert assignment.confidence == 0.95
        assert assignment.method == "keyword"
        assert assignment.event == event
        assert assignment.category == cat

    def test_event_city_assignment(self):
        """Event can be linked to cities."""
        event = Event(title="Test", event_type="concert")
        city = City(
            slug="moscow",
            name_ru="Москва",
            name_en="Moscow",
            name_ru_prepositional="в Москве",
            name_ru_genitive="Москвы",
        )
        assignment = EventCityAssignment(
            event=event, city=city, confidence=1.0, method="gazetteer"
        )
        assert assignment.city == city
        assert assignment.confidence == 1.0
        assert assignment.method == "gazetteer"


class TestContentSourceModel:
    def test_rss_source_creation(self):
        """RSS content source can be created."""
        source = ContentSource(
            name="Moscow Museums RSS",
            slug="moscow-museums",
            source_type=SourceType.RSS,
            feed_url="https://example.com/rss",
            fetch_interval_minutes=30,
            priority=1,
        )
        assert source.slug == "moscow-museums"
        assert source.source_type == SourceType.RSS
        assert source.status == SourceStatus.ACTIVE
        assert source.priority == 1

    def test_source_with_config(self):
        """Source can have fetcher-specific config."""
        source = ContentSource(
            name="API Source",
            slug="api-source",
            source_type=SourceType.API,
            feed_url="https://api.example.com/events",
            config={"api_key_env": "SOME_KEY", "endpoint": "/events"},
        )
        assert source.config["endpoint"] == "/events"


class TestCategoryModel:
    def test_category_with_keywords(self):
        """Category stores keywords for NLP classification."""
        cat = Category(
            slug="exhibitions",
            name_ru="Выставки",
            name_en="Exhibitions",
            emoji="🎨",
            keywords=["выставк", "экспозици", "галерея"],
            is_active=True,
        )
        assert cat.emoji == "🎨"
        assert "выставк" in cat.keywords


class TestCityModel:
    def test_city_with_morphology(self):
        """City stores morphological forms for gazetteer."""
        city = City(
            slug="moscow",
            name_ru="Москва",
            name_en="Moscow",
            name_ru_prepositional="в Москве",
            name_ru_genitive="Москвы",
            aliases=["msk", "москва"],
        )
        assert "в Москве" == city.name_ru_prepositional
        assert "msk" in city.aliases


class TestNotificationLog:
    def test_notification_log_creation(self):
        """Notification log entry can be created."""
        log = NotificationLog(
            user_id=123,
            notification_type="digest",
            title="Daily digest",
            was_delivered=True,
        )
        assert log.user_id == 123
        assert log.was_delivered is True
