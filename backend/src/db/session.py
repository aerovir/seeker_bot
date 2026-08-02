"""
Seeker Bot — Async database session management.

Two engines:
- ``engine`` — pooled, for the FastAPI app (reuses connections).
- ``celery_engine`` — NullPool, for Celery workers. Celery runs each
  async task via ``asyncio.run()`` in a fresh event loop (and prefork
  forks workers); a pooled engine would leak connections bound to one
  loop into another → "attached to a different loop". NullPool creates
  and closes a connection within the current loop, so it's safe.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

celery_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    pool_pre_ping=True,
    echo=False,
)

celery_session_factory = async_sessionmaker(
    celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:  # type: ignore
    """Dependency for FastAPI routes."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
