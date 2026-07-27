"""
Tests for FastAPI health endpoint.
"""

from httpx import AsyncClient, ASGITransport
import pytest


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health returns 200 with service info."""
    from src.api.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "seeker-bot-api"
    assert data["version"] == "0.1.0"
