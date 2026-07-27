"""
Pytest fixtures for Seeker Bot tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_telegram_user():
    """Create a mock Telegram user."""
    user = MagicMock()
    user.id = 123456789
    user.is_bot = False
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.language_code = "ru"
    return user


# ---- Integration test fixtures ----

@pytest.fixture(scope="session")
def db_url():
    """SQLite URL for integration tests."""
    return "sqlite+aiosqlite:///"


@pytest.fixture
async def in_memory_db():
    """Create an in-memory SQLite database with all tables."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from src.db.base import Base
    import src.db.models  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    yield session_factory

    await engine.dispose()


@pytest.fixture
async def db_session(in_memory_db):
    """Create a fresh DB session for each test."""
    async with in_memory_db() as session:
        yield session


@pytest.fixture
async def sample_cities(db_session):
    """Create sample cities in the database."""
    from src.db.models.city import City

    cities = [
        City(id=1, slug="moscow", name_ru="Москва", name_en="Moscow",
             name_ru_prepositional="в Москве", name_ru_genitive="Москвы",
             is_active=True, sort_order=1),
        City(id=2, slug="saint-petersburg", name_ru="Санкт-Петербург", name_en="Saint Petersburg",
             name_ru_prepositional="в Санкт-Петербурге", name_ru_genitive="Санкт-Петербурга",
             is_active=True, sort_order=2),
    ]
    for city in cities:
        db_session.add(city)
    await db_session.commit()
    return cities


@pytest.fixture
async def sample_categories(db_session):
    """Create sample categories in the database."""
    from src.db.models.category import Category

    categories = [
        Category(id=1, slug="exhibitions", name_ru="Выставки", name_en="Exhibitions",
                 emoji="🎨", keywords=["выставк"], is_active=True, sort_order=1),
        Category(id=2, slug="theatre", name_ru="Театр", name_en="Theatre",
                 emoji="🎭", keywords=["театр"], is_active=True, sort_order=2),
    ]
    for cat in categories:
        db_session.add(cat)
    await db_session.commit()
    return categories


@pytest.fixture
async def sample_user(db_session):
    """Create a sample user."""
    from src.db.models.user import User

    user = User(id=12345, telegram_id=12345, username="testuser",
                first_name="Test", language_code="ru")
    db_session.add(user)
    await db_session.commit()
    return user
