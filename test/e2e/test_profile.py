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


@pytest.mark.e2e
def test_get_profile_properties_endpoint():
    """Test GET /api/profile/<id>/properties returns aggregated Properties hub."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    assert list_response.status_code == 200, _err(list_response, 200)
    cards = list_response.json()
    if not cards:
        pytest.skip("No mentee cards on dashboard; cannot test properties")

    profile_id = cards[0]["_id"]
    response = requests.get(
        f"{BASE_URL}/api/profile/{profile_id}/properties",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    data = response.json()
    for key in (
        "profile",
        "status_summary",
        "sites_and_links",
        "mentor_history",
        "resource_usage",
        "celebrations",
    ):
        assert key in data, f"Response should include '{key}'"

    summary = data["status_summary"]
    for count_key in (
        "library_count",
        "now_count",
        "next_count",
        "encounters_count",
        "resources_engaged",
    ):
        assert count_key in summary, f"status_summary should include '{count_key}'"
        assert isinstance(summary[count_key], int)

    assert isinstance(data["sites_and_links"], list)
    assert isinstance(data["mentor_history"], list)
    assert isinstance(data["resource_usage"], list)
    assert isinstance(data["celebrations"], list)


@pytest.mark.e2e
def test_get_profile_properties_not_found():
    """Test GET /api/profile/<id>/properties with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/profile/000000000000000000000000/properties",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)
