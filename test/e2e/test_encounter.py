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

from .e2e_auth import get_auth_token, mint_token

BASE_URL = "http://localhost:8391"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


def _mentor_only_token(
    subject="e2e-non-owner-mentor", profile_id="A00000000000000000000006"
):
    """Mint a JWT carrying ONLY the ``mentor`` role for ownership tests.

    The default persona token (see ``e2e_auth.get_auth_token``) also carries
    ``admin``, which would bypass the owner-or-admin PATCH check. This helper
    produces a mentor-only token whose ``profile_id`` defaults to a mentor profile,
    or can be overridden to test non-owner access.
    """
    return mint_token(
        sub=subject,
        roles=["mentor"],
        profile_id=profile_id,
        customer_id="",
        mentor_id="",
        name="E2E Non-Owner Mentor",
        ttl_seconds=60 * 60,
    )


def _ensure_customer_subscription_balance(
    customer_id="d00000000000000000000002", min_balance=10
):
    """Ensure seeded test customer has sufficient active subscription balance across repeated test runs."""
    try:
        from api_utils import MongoIO

        mongo = MongoIO.get_instance()
        customer = mongo.get_document("Customer", customer_id)
        if customer and customer.get("subscriptions"):
            for sub in customer["subscriptions"]:
                if sub.get("status") == "active":
                    sub["free_encounters_remaining"] = max(
                        sub.get("free_encounters_remaining", 0), min_balance
                    )
            mongo.update_document(
                "Customer",
                customer_id,
                set_data={"subscriptions": customer["subscriptions"]},
            )
    except Exception:
        pass


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
    """POST /api/encounter returns 404 when the referenced Plan does not exist."""
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
    """POST /api/encounter succeeds with a real Plan and seeded Profile ids."""
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
    assert body["mentor_id"].lower() == "a00000000000000000000006"
    assert body["mentee_id"].lower() == "a00000000000000000000004"


@pytest.mark.e2e
def test_get_encounter_list_requires_mentee_id():
    """GET /api/encounter requires mentee_id query param; returns 400 when omitted."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/encounter", headers=headers)
    assert response.status_code == 400, _err(response, 400)


@pytest.mark.e2e
def test_get_encounter_list_scoped_by_mentee_id():
    """GET /api/encounter?mentee_id=... returns encounters for mentee."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    encounter = _create_encounter(headers)
    mentee_id = encounter["mentee_id"]

    response = requests.get(
        f"{BASE_URL}/api/encounter?mentee_id={mentee_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)
    data = response.json()
    assert isinstance(data, list)


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
    encounter = _create_encounter(admin_headers, mentor_id="507f1f77bcf86cd7994390ff")
    encounter_id = encounter["_id"]

    mentor_headers = {"Authorization": f"Bearer {_mentor_only_token()}"}
    response = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=mentor_headers,
        json={"tldr": "should be rejected"},
    )
    assert response.status_code == 403, _err(response, 403)


@pytest.mark.e2e
def test_schedule_encounters_endpoint_e2e():
    """POST /api/encounter/schedule creates recurring encounters with calculated appointments and auto-filled agenda."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-schedule-plan",
            "description": "Plan for scheduling E2E",
            "checklist": ["Review goals", "Discuss questions"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    payload = {
        "mentor_id": "A00000000000000000000006",
        "mentee_id": "A00000000000000000000002",
        "plan_id": plan_id,
        "start_date": "2024-02-01",
        "day_of_week": 1,
        "time_of_day": "14:00",
        "recurrence_days": 7,
        "count": 2,
    }

    response = requests.post(
        f"{BASE_URL}/api/encounter/schedule",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, _err(response, 201)
    encounters = response.json()
    assert isinstance(encounters, list)
    assert len(encounters) == 2

    first = encounters[0]
    assert first["status"] == "scheduled"
    assert "appointment" in first
    assert "2024-02-05" in first["appointment"]["from"]
    assert "14:00" in first["appointment"]["from"]
    assert "2024-02-05" in first["appointment"]["to"]
    assert "15:00" in first["appointment"]["to"]
    assert len(first["agenda"]) == 2
    assert first["agenda"][0]["step"] == "Review goals"
    assert first["agenda"][0]["checked"] is False
    assert "mentor_name" in first
    assert "mentee_name" in first
    assert first["mentor_name"] is not None
    assert first["mentee_name"] is not None

    second = encounters[1]
    assert second["status"] == "scheduled"
    assert "2024-02-12" in second["appointment"]["from"]
    assert "14:00" in second["appointment"]["from"]
    assert "2024-02-12" in second["appointment"]["to"]
    assert "15:00" in second["appointment"]["to"]


@pytest.mark.e2e
def test_encounter_full_lifecycle_start_patch_finish_e2e():
    """Verify schedule -> start -> patch -> finish lifecycle with status guards and subscription decrement."""
    _ensure_customer_subscription_balance()
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-lifecycle-plan",
            "description": "Plan for lifecycle",
            "checklist": ["Agenda Item 1"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    # 1. Schedule encounter for mentee with active subscription balance (Daniel / Persevere)
    schedule_payload = {
        "mentor_id": "A00000000000000000000006",
        "mentee_id": "A00000000000000000000002",
        "plan_id": plan_id,
        "start_date": "2024-03-01",
        "time_of_day": "10:00",
        "count": 1,
    }
    sched_resp = requests.post(
        f"{BASE_URL}/api/encounter/schedule",
        headers=headers,
        json=schedule_payload,
    )
    assert sched_resp.status_code == 201, _err(sched_resp, 201)
    encounter_id = sched_resp.json()[0]["_id"]

    # 2. Cannot PATCH while scheduled
    patch_early = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=headers,
        json={"summary": "early patch"},
    )
    assert patch_early.status_code == 403, _err(patch_early, 403)

    # 3. Start encounter -> status active
    start_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/start",
        headers=headers,
    )
    assert start_resp.status_code == 200, _err(start_resp, 200)
    started = start_resp.json()
    assert started["status"] == "active"
    assert started.get("mentor_name") is not None
    assert started.get("mentee_name") is not None

    # 4. Cannot re-start already active encounter
    restart_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/start",
        headers=headers,
    )
    assert restart_resp.status_code == 403, _err(restart_resp, 403)

    # 5. PATCH active encounter with allowed fields
    patch_resp = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=headers,
        json={
            "summary": "Live encounter summary",
            "tldr": "In progress TLDR",
            "transcript": "Speaker 1: Hello.",
            "agenda": [{"step": "Agenda Item 1", "checked": True}],
        },
    )
    assert patch_resp.status_code == 200, _err(patch_resp, 200)
    patched = patch_resp.json()
    assert patched["summary"] == "Live encounter summary"
    assert patched["tldr"] == "In progress TLDR"
    assert patched["transcript"] == "Speaker 1: Hello."
    assert patched["agenda"][0]["checked"] is True

    # 6. Finish encounter -> status complete
    finish_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/finish",
        headers=headers,
    )
    assert finish_resp.status_code == 200, _err(finish_resp, 200)
    finished = finish_resp.json()
    assert finished["status"] == "complete"
    assert finished.get("mentor_name") is not None
    assert finished.get("mentee_name") is not None

    # 7. Cannot PATCH after complete
    patch_late = requests.patch(
        f"{BASE_URL}/api/encounter/{encounter_id}",
        headers=headers,
        json={"summary": "late patch"},
    )
    assert patch_late.status_code == 403, _err(patch_late, 403)

    # 8. Cannot re-finish after complete
    refinish_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/finish",
        headers=headers,
    )
    assert refinish_resp.status_code == 403, _err(refinish_resp, 403)


@pytest.mark.e2e
def test_start_encounter_insufficient_subscription_balance_e2e():
    """POST /api/encounter/<id>/start returns 403 when mentee customer has 0 subscription balance."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-no-balance-plan",
            "description": "Plan",
            "checklist": ["step 1"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    # Mentee Mary (A00000000000000000000004) has customer with empty subscriptions
    schedule_payload = {
        "mentor_id": "A00000000000000000000006",
        "mentee_id": "A00000000000000000000004",
        "plan_id": plan_id,
        "start_date": "2024-03-01",
        "time_of_day": "11:00",
        "count": 1,
    }
    sched_resp = requests.post(
        f"{BASE_URL}/api/encounter/schedule",
        headers=headers,
        json=schedule_payload,
    )
    assert sched_resp.status_code == 201, _err(sched_resp, 201)
    encounter_id = sched_resp.json()[0]["_id"]

    start_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/start",
        headers=headers,
    )
    assert start_resp.status_code == 403, _err(start_resp, 403)


@pytest.mark.e2e
def test_patch_encounter_disallowed_fields_rejected_e2e():
    """PATCH /api/encounter/<id> returns 403 if disallowed fields are supplied."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create an active encounter
    encounter = _create_encounter(headers)
    encounter_id = encounter["_id"]

    for field in ["status", "mentor_id", "mentee_id", "plan_id", "appointment", "_id"]:
        bad_patch = requests.patch(
            f"{BASE_URL}/api/encounter/{encounter_id}",
            headers=headers,
            json={field: "disallowed"},
        )
        assert bad_patch.status_code == 403, _err(bad_patch, 403)


@pytest.mark.e2e
def test_encounter_mutations_non_owner_mentor_denied_e2e():
    """Start and finish mutations are denied (403) for non-owning mentors."""
    _ensure_customer_subscription_balance()
    admin_headers = {"Authorization": f"Bearer {get_auth_token()}"}
    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=admin_headers,
        json={
            "name": "e2e-nonowner-plan",
            "description": "Plan",
            "checklist": ["step 1"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    # Scheduled for mentor A00000000000000000000006
    sched_resp = requests.post(
        f"{BASE_URL}/api/encounter/schedule",
        headers=admin_headers,
        json={
            "mentor_id": "A00000000000000000000006",
            "mentee_id": "A00000000000000000000002",
            "plan_id": plan_id,
            "start_date": "2024-03-01",
            "time_of_day": "12:00",
            "count": 1,
        },
    )
    assert sched_resp.status_code == 201, _err(sched_resp, 201)
    encounter_id = sched_resp.json()[0]["_id"]

    non_owner_headers = {
        "Authorization": f"Bearer {_mentor_only_token(profile_id='A00000000000000000000010')}"
    }

    # Non-owner cannot start
    start_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/start",
        headers=non_owner_headers,
    )
    assert start_resp.status_code == 403, _err(start_resp, 403)

    # Start with admin
    admin_start = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/start",
        headers=admin_headers,
    )
    assert admin_start.status_code == 200, _err(admin_start, 200)

    # Non-owner cannot finish
    finish_resp = requests.post(
        f"{BASE_URL}/api/encounter/{encounter_id}/finish",
        headers=non_owner_headers,
    )
    assert finish_resp.status_code == 403, _err(finish_resp, 403)


@pytest.mark.e2e
def test_encounter_name_enrichment_get_endpoints_e2e():
    """GET /api/encounter/<id> and GET /api/encounter?mentee_id=... return enriched mentor_name and mentee_name."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    plan_response = requests.post(
        f"{BASE_URL}/api/plan",
        headers=headers,
        json={
            "name": "e2e-enrich-plan",
            "description": "Plan",
            "checklist": ["step 1"],
        },
    )
    assert plan_response.status_code == 201, _err(plan_response, 201)
    plan_id = plan_response.json()["_id"]

    # Create encounter with seeded IDs (marti mentor, daniel mentee)
    data = {
        "mentor_id": "A00000000000000000000006",
        "mentee_id": "A00000000000000000000002",
        "plan_id": plan_id,
        "status": "active",
        "summary": "Enriched test",
        "tldr": "Enriched",
    }
    create_resp = requests.post(f"{BASE_URL}/api/encounter", headers=headers, json=data)
    assert create_resp.status_code == 201, _err(create_resp, 201)
    encounter_id = create_resp.json()["_id"]

    # 1. GET by ID
    get_resp = requests.get(f"{BASE_URL}/api/encounter/{encounter_id}", headers=headers)
    assert get_resp.status_code == 200, _err(get_resp, 200)
    single = get_resp.json()
    assert "mentor_name" in single
    assert "mentee_name" in single
    assert single["mentor_name"] is not None
    assert single["mentee_name"] is not None

    # 2. GET list by mentee_id
    list_resp = requests.get(
        f"{BASE_URL}/api/encounter?mentee_id=A00000000000000000000002",
        headers={**headers, "size": "100"},
    )
    assert list_resp.status_code == 200, _err(list_resp, 200)
    enc_list = list_resp.json()
    assert len(enc_list) > 0
    matched = [e for e in enc_list if e["_id"] == encounter_id]
    assert len(matched) == 1
    assert matched[0]["mentor_name"] is not None
    assert matched[0]["mentee_name"] is not None
