"""Unit tests for Flask API (app.py)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

# Import app after potential env changes
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_recommend_missing_location_get_returns_400(client):
    r = client.get("/recommend")
    assert r.status_code == 400
    assert "location" in r.get_json().get("error", "").lower() or "location" in str(r.get_json())


def test_recommend_missing_location_post_returns_400(client):
    r = client.post("/recommend", json={})
    assert r.status_code == 400


def test_recommend_value_error_openai_key_returns_500(client):
    """Server config error (missing OPENAI_API_KEY) must return 500, not 400."""
    with patch("app.get_weekend_recommendation", side_effect=ValueError(
        "OPENAI_API_KEY is not set. Create an API key at https://platform.openai.com/api-keys "
        "and set it in your environment or .env file."
    )):
        r = client.get("/recommend?location=Paris")
    assert r.status_code == 500
    assert "OPENAI_API_KEY" in r.get_json().get("error", "")


def test_recommend_success_returns_200(client):
    with patch("app.get_weekend_recommendation", return_value="Visit the Eiffel Tower."):
        r = client.get("/recommend?location=Paris")
    assert r.status_code == 200
    data = r.get_json()
    assert data["location"] == "Paris"
    assert data["recommendation"] == "Visit the Eiffel Tower."
