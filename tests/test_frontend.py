"""Tests for the static frontend and root landing page endpoint."""

from fastapi.testclient import TestClient


def test_root_serves_static_index_html(client: TestClient):
    """Test GET / returns 200 OK with the self-contained static HTML single-page app."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "<title>" in html
    assert "Daaruka.Earth" in html
    assert "id=\"chatForm\"" in html or "chatForm" in html
    assert "id=\"messageInput\"" in html or "messageInput" in html
    assert "/api/v1/chat" in html
