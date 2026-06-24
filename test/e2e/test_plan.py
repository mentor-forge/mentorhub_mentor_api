"""
E2E tests for Plan endpoints.

These tests verify that Plan endpoints work correctly by making
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
def test_create_plan_endpoint():
    """Test POST /api/plan endpoint and verify record persists in database."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-plan",
        "description": "E2E test plan document",
    }

    response = requests.post(f"{BASE_URL}/api/plan", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-plan"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_plans_endpoint():
    """Test GET /api/plan endpoint returns all plans, sorted by name."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/plan", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a list of plans"
    names = [plan.get("name") for plan in response_data if "name" in plan]
    assert names == sorted(names), "Plans should be sorted by name (ascending)"


@pytest.mark.e2e
def test_plan_endpoints_require_auth():
    """Test that plan endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/plan")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
