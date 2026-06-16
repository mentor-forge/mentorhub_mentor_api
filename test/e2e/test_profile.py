"""
E2E tests for Profile endpoints (consume-style, read-only).

These tests verify that Profile endpoints work correctly by making
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
def test_get_profiles_endpoint():
    """Test GET /api/profile returns the Mentor Dashboard array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(
        response_data, list
    ), "Response should be a list of dashboard cards"
    for card in response_data:
        assert "_id" in card, "Each card should have an '_id'"
        assert "name" in card, "Each card should have a 'name'"
        assert "progress" in card, "Each card should have a 'progress' object"
        progress = card["progress"]
        assert set(["library", "now", "next"]).issubset(
            progress.keys()
        ), "progress should report library/now/next counts"
        assert (
            "last_encounter" in card
        ), "Each card should have a 'last_encounter' field"


@pytest.mark.e2e
def test_get_profile_not_found():
    """Test GET /api/profile/<id> with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/profile/000000000000000000000000",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_profile_endpoints_require_auth():
    """Test that profile endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/profile")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
