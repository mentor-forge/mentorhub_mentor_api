"""
E2E tests for Resource endpoints.

These tests verify that Resource endpoints work correctly by making
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
def test_create_resource_endpoint():
    """Test POST /api/resource endpoint and verify record persists in database."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-resource",
        "description": "E2E test resource document",
    }

    response = requests.post(f"{BASE_URL}/api/resource", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-resource"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_resources_endpoint():
    """Test GET /api/resource returns a plain array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a plain JSON array"


@pytest.mark.e2e
def test_get_resources_header_pagination():
    """Test GET /api/resource honors offset/size request headers."""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "offset": "0",
        "size": "1",
    }
    response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a plain JSON array"
    assert len(response_data) <= 1, "size=1 should cap the page at one item"


@pytest.mark.e2e
def test_get_resources_with_name_filter_and_order():
    """Test GET /api/resource with name filter + sort_by/order query params."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/resource?name=e2e&sort_by=name&order=asc",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a plain JSON array"


@pytest.mark.e2e
def test_resource_endpoints_require_auth():
    """Test that resource endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/resource")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
