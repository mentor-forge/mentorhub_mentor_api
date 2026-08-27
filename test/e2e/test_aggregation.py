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
    """Test GET /api/aggregation/{resource_id} returns composite detail."""
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

    detail = response.json()
    assert "aggregation" in detail, "Detail should include aggregation"
    assert "notes" in detail, "Detail should include notes"
    assert isinstance(detail["notes"], list), "notes should be an array"
    assert detail["aggregation"] is not None
    agg = detail["aggregation"]
    assert agg.get("_id") == resource_id or agg.get("resource_id") == resource_id


@pytest.mark.e2e
def test_get_aggregation_detail_creates_when_missing():
    """Test GET /api/aggregation/{resource_id} creates aggregation when missing."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    synthetic_id = "507f1f77bcf86cd799439999"
    response = requests.get(
        f"{BASE_URL}/api/aggregation/{synthetic_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    detail = response.json()
    assert "aggregation" in detail
    assert "notes" in detail
    assert detail["aggregation"] is not None
    assert detail["aggregation"].get("resource_id") == synthetic_id


@pytest.mark.e2e
def test_aggregation_endpoint_requires_auth():
    """Test that aggregation endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/aggregation/507f1f77bcf86cd799439011")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
