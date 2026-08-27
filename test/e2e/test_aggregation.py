"""
E2E tests for Aggregation endpoints.
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
def test_get_aggregation_detail_endpoint():
    """Test GET /api/aggregation/{resource_id} returns aggregation document."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for aggregation test")

    resource_id = resources[0]["_id"]
    response = requests.get(
        f"{BASE_URL}/api/aggregation/{resource_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    agg = response.json()
    if agg is not None:
        assert "_id" in agg
        assert "hits" in agg


@pytest.mark.e2e
def test_get_aggregation_nonexistent_resource():
    """Test GET /api/aggregation/{resource_id} returns null for non-existent resource."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    synthetic_id = "507f1f77bcf86cd799439999"
    response = requests.get(
        f"{BASE_URL}/api/aggregation/{synthetic_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)
    assert response.json() is None


@pytest.mark.e2e
def test_aggregation_endpoint_requires_auth():
    """Test that aggregation endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/aggregation/507f1f77bcf86cd799439011")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
