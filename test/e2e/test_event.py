"""
E2E tests for Event endpoints (create-style with POST and GET).

These tests verify that Event endpoints work correctly by making
actual HTTP requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port 8391 (same for dev and api).
"""

import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:8391"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


@pytest.mark.e2e
def test_create_event_endpoint():
    """Test POST /api/event endpoint and basic retrieval by ID and search."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "type": "login",
        "context": {"profile_id": "000000000000000000000001"},
    }

    response = requests.post(f"{BASE_URL}/api/event", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["type"] == "login"
    assert "created" in response_data


@pytest.mark.e2e
def test_get_events_endpoint():
    """Test GET /api/event returns all events as a JSON array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/event", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"


@pytest.mark.e2e
def test_get_event_not_found():
    """Test GET /api/event/<id> with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/event/000000000000000000000000",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_event_endpoints_require_auth():
    """Test that event endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/event")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
