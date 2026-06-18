"""
E2E tests for Mentee endpoints.

These tests verify that Mentee endpoints work correctly by making actual HTTP
requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port 8391 (same for dev and api).
"""

import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:8391"

# A stable mentee Profile id used to exercise the create-if-missing read path.
# The Mentee document is keyed by this id; reusing it keeps the test idempotent.
PROFILE_ID = "507f1f77bcf86cd7994390e2"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


@pytest.mark.e2e
def test_get_mentee_auto_create_and_idempotent():
    """GET auto-creates a valid Mentee document and is idempotent per profile_id."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    first = requests.get(f"{BASE_URL}/api/mentee/{PROFILE_ID}", headers=headers)
    assert first.status_code == 200, _err(first, 200)
    first_doc = first.json()
    assert "_id" in first_doc, "Response missing '_id' key"
    assert first_doc["profile_id"] == PROFILE_ID
    assert first_doc["status"] == "active"
    assert "created" in first_doc
    assert "saved" in first_doc

    # A second GET for the same profile must return the same document (no dupes).
    second = requests.get(f"{BASE_URL}/api/mentee/{PROFILE_ID}", headers=headers)
    assert second.status_code == 200, _err(second, 200)
    assert second.json()["_id"] == first_doc["_id"]


@pytest.mark.e2e
def test_patch_mentee_round_trip():
    """PATCH updates a Mentee document and the change is visible on re-read."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    created = requests.get(f"{BASE_URL}/api/mentee/{PROFILE_ID}", headers=headers)
    assert created.status_code == 200, _err(created, 200)
    mentee_id = created.json()["_id"]

    payload = {"focus": "E2E focus area", "notes": "E2E mentor notes"}
    patched = requests.patch(
        f"{BASE_URL}/api/mentee/{mentee_id}", headers=headers, json=payload
    )
    assert patched.status_code == 200, _err(patched, 200)
    patched_doc = patched.json()
    assert patched_doc["focus"] == "E2E focus area"
    assert patched_doc["notes"] == "E2E mentor notes"
    assert "saved" in patched_doc

    # Re-read via the profile to confirm the update persisted.
    reread = requests.get(f"{BASE_URL}/api/mentee/{PROFILE_ID}", headers=headers)
    assert reread.status_code == 200, _err(reread, 200)
    assert reread.json()["focus"] == "E2E focus area"


@pytest.mark.e2e
def test_mentee_endpoints_require_auth():
    """Test that mentee endpoints require authentication."""
    get_response = requests.get(f"{BASE_URL}/api/mentee/{PROFILE_ID}")
    assert (
        get_response.status_code == 401
    ), f"Expected 401, got {get_response.status_code}"

    patch_response = requests.patch(
        f"{BASE_URL}/api/mentee/{PROFILE_ID}", json={"focus": "nope"}
    )
    assert (
        patch_response.status_code == 401
    ), f"Expected 401, got {patch_response.status_code}"
