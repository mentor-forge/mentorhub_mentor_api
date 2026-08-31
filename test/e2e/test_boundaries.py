"""
E2E adversarial boundary checks for Mentor API craftsmanship invariants.

These tests verify architectural contracts that happy-path suites can miss:
- list GETs are JSON arrays with no legacy X-Pagination-* headers
- shared outbound filtering differs for admin vs non-admin
- hidden/archived documents return 404 (not 403)
- Event by-id uses the same outbound scope as list GET
- live OpenAPI matches the 1.0.0 aggregation/list contracts
"""

import pytest
import requests

from .e2e_auth import get_auth_token, mint_token

BASE_URL = "http://localhost:8391"

# Seeded mentor persona with no admin role (least privilege for outbound tests).
_MENTOR_ONLY_PROFILE_ID = "A00000000000000000000006"
_OTHER_PROFILE_ID = "A00000000000000000000013"


def _err(response, expected):
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


def _mentor_only_token():
    return mint_token(
        sub="e2e-mentor-only",
        roles=["mentor"],
        profile_id=_MENTOR_ONLY_PROFILE_ID,
        customer_id="D00000000000000000000002",
        mentor_id=_MENTOR_ONLY_PROFILE_ID,
        name="E2E Mentor Only",
        ttl_seconds=3600,
    )


def _assert_list_contract(response):
    """Assert 1.0.0 list GET shape: JSON array, no pagination response headers."""
    assert response.status_code == 200, _err(response, 200)
    body = response.json()
    assert isinstance(body, list), "List GET must return a plain JSON array"
    assert not any(
        key.lower().startswith("x-pagination-") for key in response.headers
    ), f"Legacy X-Pagination-* headers must not appear: {dict(response.headers)}"
    return body


@pytest.mark.e2e
def test_list_gets_have_no_pagination_response_headers():
    """Resource/Path/Plan/Event lists must not revive X-Pagination-* headers."""
    headers = {"Authorization": f"Bearer {get_auth_token()}", "size": "5"}
    for path in ("/api/resource", "/api/path", "/api/plan", "/api/event"):
        response = requests.get(f"{BASE_URL}{path}", headers=headers)
        _assert_list_contract(response)


@pytest.mark.e2e
def test_archived_resource_hidden_for_non_admin():
    """Archived Resource is visible to admin but 404 for mentor-only (not 403)."""
    admin_headers = {"Authorization": f"Bearer {get_auth_token()}"}
    created = requests.post(
        f"{BASE_URL}/api/resource",
        headers=admin_headers,
        json={"name": "e2e-archived-resource", "description": "boundary"},
    )
    assert created.status_code == 201, _err(created, 201)
    resource_id = created.json()["_id"]

    patched = requests.patch(
        f"{BASE_URL}/api/resource/{resource_id}",
        headers=admin_headers,
        json={"status": "archived"},
    )
    assert patched.status_code == 200, _err(patched, 200)

    admin_get = requests.get(
        f"{BASE_URL}/api/resource/{resource_id}",
        headers=admin_headers,
    )
    assert admin_get.status_code == 200, _err(admin_get, 200)

    mentor_headers = {"Authorization": f"Bearer {_mentor_only_token()}"}
    mentor_get = requests.get(
        f"{BASE_URL}/api/resource/{resource_id}",
        headers=mentor_headers,
    )
    assert mentor_get.status_code == 404, _err(mentor_get, 404)

    agg = requests.get(
        f"{BASE_URL}/api/aggregation/{resource_id}",
        headers=mentor_headers,
    )
    assert agg.status_code == 200, _err(agg, 200)
    assert agg.json() is None


@pytest.mark.e2e
def test_event_by_id_respects_outbound_scope():
    """Event by-id must 404 for a mentor whose profile_id is outside the event."""
    admin_headers = {"Authorization": f"Bearer {get_auth_token()}"}
    created = requests.post(
        f"{BASE_URL}/api/event",
        headers=admin_headers,
        json={"type": "login"},
    )
    assert created.status_code == 201, _err(created, 201)
    event_id = created.json()["_id"]

    admin_get = requests.get(
        f"{BASE_URL}/api/event/{event_id}",
        headers=admin_headers,
    )
    assert admin_get.status_code == 200, _err(admin_get, 200)

    mentor_token = mint_token(
        sub="e2e-event-scope",
        roles=["mentor"],
        profile_id=_OTHER_PROFILE_ID,
        customer_id="D00000000000000000000006",
        mentor_id="",
        name="E2E Event Scope",
        ttl_seconds=3600,
    )
    mentor_headers = {"Authorization": f"Bearer {mentor_token}"}
    mentor_get = requests.get(
        f"{BASE_URL}/api/event/{event_id}",
        headers=mentor_headers,
    )
    assert mentor_get.status_code == 404, _err(mentor_get, 404)


@pytest.mark.e2e
def test_live_openapi_matches_list_and_aggregation_contracts():
    """Served OpenAPI must document array lists and nullable aggregation."""
    response = requests.get(f"{BASE_URL}/docs/openapi.yaml")
    assert response.status_code == 200, _err(response, 200)
    text = response.text
    assert "X-Pagination-Offset" not in text
    assert "X-Pagination-Size" not in text
    assert "X-Pagination-Returned" not in text
    assert "AggregationDetail" not in text
    assert "operationId: getAggregation" in text
    assert "nullable: true" in text
