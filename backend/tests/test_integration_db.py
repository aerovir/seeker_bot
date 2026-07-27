"""
Integration tests — database operations with SQLite in-memory.

Tests: models, repositories, services with real DB transactions.
"""

import pytest
from datetime import datetime, timezone


class TestModelIntegration:
    """Integration tests for model CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_user_in_db(self, db_session):
        """User can be created and queried from DB."""
        from src.db.models.user import User

        user = User(id=999, telegram_id=999, username="integration_test")
        db_session.add(user)
        await db_session.commit()

        # Query back
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.telegram_id == 999)
        )
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.username == "integration_test"
        assert found.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_with_preferences(self, db_session, sample_cities, sample_categories):
        """User can have city and category preferences."""
        from src.db.models.user import User, UserCityPreference, UserCategoryPreference

        user = User(id=888, telegram_id=888)
        db_session.add(user)

        pref_city = UserCityPreference(user_id=888, city_id=1)
        pref_cat = UserCategoryPreference(user_id=888, category_id=1)
        db_session.add(pref_city)
        db_session.add(pref_cat)
        await db_session.commit()

        # Verify through relationships
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(User)
            .where(User.id == 888)
            .options(selectinload(User.city_preferences), selectinload(User.category_preferences))
        )
        found = result.scalar_one()

        assert len(found.city_preferences) == 1
        assert found.city_preferences[0].city_id == 1
        assert len(found.category_preferences) == 1

    @pytest.mark.asyncio
    async def test_lifecycle_defaults(self, db_session):
        """Models use correct defaults in DB."""
        from src.db.models.user import User
        from src.db.models.event import Event
        from src.common.constants import EventStatus

        user = User(id=777, telegram_id=777)
        db_session.add(user)

        event = Event(title="Integration Event", event_type="concert")
        db_session.add(event)
        await db_session.commit()

        assert user.language_code == "ru"
        assert user.is_active is True
        assert event.status == EventStatus.PENDING
        assert event.currency == "RUB"


class TestDataIntegrity:
    """Tests for data integrity constraints."""

    @pytest.mark.asyncio
    async def test_unique_telegram_id(self, db_session):
        """Two users cannot have the same telegram_id."""
        from src.db.models.user import User

        db_session.add(User(id=101, telegram_id=101))
        await db_session.commit()

        db_session.add(User(id=102, telegram_id=101))
        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_cascade_delete_user(self, db_session):
        """Deleting a user cascades to preferences."""
        from src.db.models.user import User, UserCityPreference

        user = User(id=202, telegram_id=202)
        db_session.add(user)
        await db_session.flush()

        pref = UserCityPreference(user_id=202, city_id=1)
        db_session.add(pref)
        await db_session.commit()

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(UserCityPreference).where(UserCityPreference.user_id == 202)
        )
        assert result.scalar_one_or_none() is None


class TestCategoryClassifierIntegration:
    """Category classifier with real data from DB."""

    @pytest.mark.asyncio
    async def test_classify_with_db_categories(self, db_session, sample_categories):
        """Category classifier uses categories from database."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(db_session)
        await classifier.load_categories()

        assert len(classifier.categories) == 2

        result = classifier.classify("Новая выставка в галерее", None)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_classify_no_match_db(self, db_session):
        """No match when no categories in DB."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(db_session)
        await classifier.load_categories()

        assert classifier.categories == []

        result = classifier.classify("Выставка в галерее", None)
        assert result == []


class TestCityClassifierIntegration:
    """City classifier with real data from DB."""

    @pytest.mark.asyncio
    async def test_build_index_from_db(self, db_session, sample_cities):
        """CityClassifier builds index from database cities."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(db_session)
        await classifier.build_index()

        assert len(classifier.city_forms) > 0

        result = classifier.extract("Событие в Москве", None)
        assert len(result) == 1
        assert result[0][0] == 1  # Moscow
