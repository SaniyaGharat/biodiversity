"""Pytest configuration and shared fixtures for Daaruka test suite."""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from daaruka.main import create_application
from daaruka.core.config import settings


@pytest.fixture(scope="session")
def app():
    """Application fixture initialized for the test session."""
    settings.DEBUG = True
    return create_application()


@pytest.fixture(scope="session")
def client(app) -> Generator[TestClient, None, None]:
    """Synchronous test client fixture."""
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> AsyncClient:
    """Asynchronous test client fixture for async endpoint tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
