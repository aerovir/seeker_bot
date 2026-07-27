"""
Tests for API routers — TMA endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def override_dependencies():
    """Override FastAPI dependencies with mocks."""
    from src.api.app import app
    from src.db.session import get_session

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(return_value=None)

    app.dependency_overrides[get_session] = lambda: mock_session

    yield mock_session

    app.dependency_overrides.clear()


class TestPublicEndpoints:
    @pytest.mark.asyncio
    async def test_get_feed(self):
        """GET /api/v1/feed returns feed with pagination."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/feed")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_get_cities(self):
        """GET /api/v1/cities returns list of cities."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/cities")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_categories(self):
        """GET /api/v1/categories returns list of categories."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/categories")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_event_not_found(self):
        """GET /api/v1/events/999 returns 404."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/events/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_health(self):
        """GET /health returns ok."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthenticatedEndpoints:
    @pytest.mark.asyncio
    async def test_get_preferences_unauthorized(self):
        """GET /api/v1/preferences/ returns 401 without auth."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/preferences/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_put_preferences_unauthorized(self):
        """PUT /api/v1/preferences/ returns 401 without auth."""
        from src.api.app import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/preferences/",
                json={"city_ids": [1, 2], "category_ids": [1, 2, 3]},
            )

        assert response.status_code == 401
