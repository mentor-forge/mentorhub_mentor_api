"""
E2E tests for Encounter endpoints.

These tests verify that Encounter endpoints work correctly by making
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
def test_create_encounter_from_plan_endpoint():
    """POST /api/encounter auto-fills agenda from the referenced Plan's steps."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a Plan with a checklist (exposed as `steps`) to derive the agenda.
    plan_steps = ["review goals", "discuss blockers"]
    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-encounter-plan",
            "description": "E2E plan for encounter agenda autofill",
            "steps": plan_steps,
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    # Any valid ObjectId strings are acceptable for the mentor/mentee references.
    data = {
        "mentor_id": "507f1f77bcf86cd799439011",
        "mentee_id": "507f1f77bcf86cd799439012",
        "plan_id": plan_id,
        "status": "active",
        "summary": "E2E test encounter summary",
        "tldr": "E2E test encounter",
        # Client-supplied agenda must be ignored/overwritten by the Plan agenda.
        "agenda": [{"step": "client provided", "checked": True}],
    }

    response = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["summary"] == "E2E test encounter summary"
    assert "created" in response_data
    assert "saved" in response_data
    assert response_data.get("agenda") == [
        {"step": "review goals", "checked": False},
        {"step": "discuss blockers", "checked": False},
    ], _err(response, "agenda derived from plan steps")


@pytest.mark.e2e
def test_create_encounter_missing_required_field():
    """POST /api/encounter returns 400 when a required reference id is missing."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "mentee_id": "507f1f77bcf86cd799439012",
        "plan_id": "507f1f77bcf86cd799439013",
        "status": "active",
    }

    response = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert response.status_code == 400, _err(response, 400)


@pytest.mark.e2e
def test_get_encounters_endpoint():
    """Test GET /api/encounter endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/encounter", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(
        response_data, dict
    ), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_encounters_with_name_filter():
    """Test GET /api/encounter with name query parameter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/encounter?name=e2e", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(
        response_data, dict
    ), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_encounter_endpoints_require_auth():
    """Test that encounter endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/encounter")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
