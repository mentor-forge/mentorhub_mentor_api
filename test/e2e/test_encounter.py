"""
E2E tests for Encounter endpoints.

These tests verify that Encounter endpoints work correctly by making
actual HTTP requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port 8391 (same for dev and api).
"""

import os
import time

import jwt
import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:8391"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


def _mentor_only_token(subject="e2e-non-owner-mentor"):
    """Mint a JWT carrying ONLY the ``mentor`` role for ownership tests.

    The default persona token (see ``e2e_auth.get_auth_token``) also carries
    ``admin``, which would bypass the owner-or-admin PATCH check. This helper
    produces a mentor-only token whose resolved Profile (if any) will not own a
    freshly created encounter, so PATCH is expected to be denied (403).
    """
    secret = os.environ.get("JWT_SECRET") or "local-dev-jwt-secret-fixed"
    issuer = os.environ.get("JWT_ISSUER") or "dev-idp"
    audience = os.environ.get("JWT_AUDIENCE") or "dev-api"
    algorithm = os.environ.get("JWT_ALGORITHM") or "HS256"
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "iat": now,
        "exp": now + 60 * 60,
        "roles": ["mentor"],
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def _create_encounter(headers, mentor_id="507f1f77bcf86cd799439011"):
    """Create an encounter (deriving agenda from a fresh Plan) and return it."""
    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-encounter-rbac-plan",
            "description": "E2E plan for encounter RBAC",
            "checklist": ["review goals"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    data = {
        "mentor_id": mentor_id,
        "mentee_id": "507f1f77bcf86cd799439012",
        "plan_id": plan_id,
        "status": "active",
        "summary": "E2E RBAC encounter",
        "tldr": "E2E RBAC",
    }
    response = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)
    return response.json()


@pytest.mark.e2e
def test_create_encounter_from_plan_endpoint():
    """POST /api/encounter auto-fills agenda from the referenced Plan's steps."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a Plan with a checklist to derive the encounter agenda.
    plan_steps = ["review goals", "discuss blockers"]
    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-encounter-plan",
            "description": "E2E plan for encounter agenda autofill",
            "checklist": plan_steps,
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
def test_create_encounter_unknown_plan_returns_404():
    """POST /api/encounter returns 404 when the referenced Plan does not exist.

    The create path resolves the referenced Plan before persisting; a
    well-formed but unknown ``plan_id`` surfaces as ``HTTPNotFound`` (404).
    """
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "mentor_id": "507f1f77bcf86cd799439011",
        "mentee_id": "507f1f77bcf86cd799439012",
        # Valid ObjectId shape, but no such Plan exists in the seeded database.
        "plan_id": "507f1f77bcf86cd799439013",
        "status": "active",
    }

    response = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_create_encounter_with_seeded_profile_ids():
    """POST /api/encounter succeeds with a real Plan and seeded Profile ids.

    ``mentor_id`` and ``mentee_id`` use Profile documents loaded into the
    database on startup (``marti`` and ``mary``); ``plan_id`` is created via
    the Plan endpoint so every reference id is valid.
    """
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-encounter-valid-ids-plan",
            "description": "E2E plan for valid reference id create",
            "checklist": ["review goals"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    data = {
        # Seeded Profile ids (see Profile test data): marti (mentor), mary (mentee).
        "mentor_id": "A00000000000000000000006",
        "mentee_id": "A00000000000000000000004",
        "plan_id": plan_id,
        "status": "active",
        "summary": "E2E encounter with seeded profile ids",
        "tldr": "E2E seeded ids",
    }

    response = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    body = response.json()
    assert "_id" in body, "Response missing '_id' key"
    assert body["mentor_id"] == "A00000000000000000000006"
    assert body["mentee_id"] == "A00000000000000000000004"


@pytest.mark.e2e
def test_get_encounter_list_endpoint_removed():
    """GET /api/encounter (list) no longer exists; expect 404/405, never 200."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/encounter", headers=headers)
    assert response.status_code in (404, 405), _err(response, "404 or 405")


@pytest.mark.e2e
def test_encounter_endpoints_require_auth():
    """Test that encounter endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/encounter/507f1f77bcf86cd799439011")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.e2e
def test_update_encounter_owner_or_admin_allowed():
    """PATCH /api/encounter/<id> succeeds for an admin/owning caller (200)."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    encounter = _create_encounter(headers)
    encounter_id = encounter["_id"]

    response = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=headers,
        json={"tldr": "updated by admin"},
    )
    assert response.status_code == 200, _err(response, 200)
    assert response.json().get("tldr") == "updated by admin"


@pytest.mark.e2e
def test_update_encounter_non_owner_mentor_denied():
    """PATCH /api/encounter/<id> is denied (403) for a non-owning mentor."""
    admin_headers = {"Authorization": f"Bearer {get_auth_token()}"}
    # Create an encounter owned by an arbitrary mentor id (not the caller below).
    encounter = _create_encounter(admin_headers, mentor_id="507f1f77bcf86cd7994390ff")
    encounter_id = encounter["_id"]

    mentor_headers = {"Authorization": f"Bearer {_mentor_only_token()}"}
    response = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=mentor_headers,
        json={"tldr": "should be rejected"},
    )
    assert response.status_code == 403, _err(response, 403)
