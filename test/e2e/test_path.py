"""
E2E tests for Path endpoints.

These tests verify that Path endpoints work correctly by making
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


@pytest.mark.e2e
def test_create_path_endpoint():
    """Test POST /api/path endpoint and verify record persists in database."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-path",
        "description": "E2E test path document",
    }

    response = requests.post(f"{BASE_URL}/api/path", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-path"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_paths_endpoint():
    """Test GET /api/path endpoint returns all paths as an array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/path", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array of paths"


@pytest.mark.e2e
def test_get_paths_with_name_filter():
    """Test GET /api/path with name query parameter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/path?name=e2e", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array of paths"


@pytest.mark.e2e
def test_path_endpoints_require_auth():
    """Test that path endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/path")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def _mint_token(roles):
    """Mint a persona JWT with the given roles for RBAC e2e cases."""
    secret = os.environ.get("JWT_SECRET") or "local-dev-jwt-secret-fixed"
    issuer = os.environ.get("JWT_ISSUER") or "dev-idp"
    audience = os.environ.get("JWT_AUDIENCE") or "dev-api"
    algorithm = os.environ.get("JWT_ALGORITHM") or "HS256"
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": "e2e-rbac",
        "iat": now,
        "exp": now + 3600,
        "roles": list(roles),
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token.decode("ascii") if isinstance(token, bytes) else token


@pytest.mark.e2e
def test_patch_path_allowed_for_privileged():
    """PATCH /api/path/<id> succeeds for an admin/mentor caller."""
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    created = requests.post(
        f"{BASE_URL}/api/path", headers=headers, json={"name": "e2e-patch-path"}
    )
    assert created.status_code == 201, _err(created, 201)
    path_id = created.json()["_id"]

    response = requests.patch(
        f"{BASE_URL}/api/path/{path_id}",
        headers=headers,
        json={"description": "updated by e2e"},
    )
    assert response.status_code == 200, _err(response, 200)
    assert response.json()["description"] == "updated by e2e"


@pytest.mark.e2e
def test_patch_path_denied_for_non_privileged():
    """PATCH /api/path/<id> is denied (403) for a non-mentor/admin caller."""
    admin_headers = {"Authorization": f"Bearer {get_auth_token()}"}
    created = requests.post(
        f"{BASE_URL}/api/path", headers=admin_headers, json={"name": "e2e-patch-deny"}
    )
    assert created.status_code == 201, _err(created, 201)
    path_id = created.json()["_id"]

    headers = {"Authorization": f"Bearer {_mint_token(['mentee'])}"}
    response = requests.patch(
        f"{BASE_URL}/api/path/{path_id}",
        headers=headers,
        json={"description": "nope"},
    )
    assert response.status_code == 403, _err(response, 403)
