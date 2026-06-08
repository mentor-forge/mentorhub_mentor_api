"""
E2E tests for {{item}} endpoints (create-style with POST and GET).

These tests verify that {{item}} endpoints work correctly by making
actual HTTP requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port {{repo.port}} (same for dev and api).
"""
import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:{{repo.port}}"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


@pytest.mark.e2e
def test_create_{{item | lower}}_endpoint():
    """Test POST /api/{{item | lower}} endpoint and basic retrieval by ID and search."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-{{item | lower}}",
        "description": "E2E test {{item | lower}} document",
    }

    response = requests.post(f"{BASE_URL}/api/{{item | lower}}", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-{{item | lower}}"
    assert "created" in response_data


@pytest.mark.e2e
def test_get_{{item | lower}}s_endpoint():
    """Test GET /api/{{item | lower}} endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/{{item | lower}}", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_{{item | lower}}_not_found():
    """Test GET /api/{{item | lower}}/<id> with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/{{item | lower}}/000000000000000000000000",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_{{item | lower}}_endpoints_require_auth():
    """Test that {{item | lower}} endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/{{item | lower}}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

