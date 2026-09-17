"""Unit and integration tests for service health endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient


def test_top_level_health_check_sync(client: TestClient):
    """Test top-level /health endpoint returns 200 OK and expected structure."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "daaruka-backend"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data

    # Verify timestamp parses as valid ISO format
    parsed_time = datetime.fromisoformat(data["timestamp"])
    assert parsed_time is not None


def test_v1_health_check_sync(client: TestClient):
    """Test versioned /api/v1/health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "daaruka-backend"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_check_async(async_client: AsyncClient):
    """Test health check using asynchronous HTTP client."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "daaruka-backend"


def test_invalid_route_returns_404(client: TestClient):
    """Test non-existent route properly returns 404 Not Found."""
    response = client.get("/non-existent-route")
    assert response.status_code == 404
