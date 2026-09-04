"""E2E Bearer JWTs aligned with the umbrella welcome page (``welcome-auth.js``) personas.

Tokens now carry the full Developer-Edition claim set — ``roles`` plus the custom
claims ``profile_id`` (required), ``customer_id``, and ``mentor_id`` (and ``name``) —
matching the payload minted by ``../mentorhub/welcome-auth.js``.

Uses ``JWT_SECRET``, ``JWT_ISSUER``, ``JWT_AUDIENCE``, and ``JWT_ALGORITHM`` from the
environment when set (``pipenv run e2e`` exports the Developer Edition defaults). Override
those variables to match a non-default API stack (same values the container / compose uses).
"""

from __future__ import annotations

import os
import time

import jwt

# Defaults match welcome-auth.js static welcome tokens (HS256, iss dev-idp, aud dev-api)
# and the Pipfile dev/e2e scripts.
_DEFAULT_JWT_SECRET = "local-dev-jwt-secret-fixed"
_DEFAULT_JWT_ISSUER = "dev-idp"
_DEFAULT_JWT_AUDIENCE = "dev-api"
_DEFAULT_JWT_ALGORITHM = "HS256"

# The default persona keeps ``sub="adam"`` and resolves its Profile by the
# required ``profile_id`` claim. It retains both ``admin`` and ``mentor`` so
# role-gated reads and the owner-or-admin
# PATCH bypass in the Encounter/Path tests keep passing. ``profile_id`` is a real
# seeded Profile id (Sam Admin) to satisfy the now-required claim.
_E2E_SUBJECT = "adam"
_E2E_NAME = "Adam Admin"
_E2E_ROLES = ("admin", "mentor")
_E2E_PROFILE_ID = "A00000000000000000000013"
_E2E_CUSTOMER_ID = "D00000000000000000000006"
_E2E_MENTOR_ID = ""


def mint_token(
    sub,
    roles,
    profile_id,
    customer_id="",
    mentor_id="",
    name=None,
    ttl_seconds=10 * 365 * 24 * 60 * 60,
) -> str:
    """Mint a persona JWT carrying the full Developer-Edition claim set.

    ``profile_id`` is required (as is ``roles``); ``customer_id``/``mentor_id``
    default to empty strings, mirroring the personas in ``welcome-auth.js`` that
    do not carry those references. Environment overrides for the JWT
    secret/issuer/audience/algorithm are honored.
    """
    secret = os.environ.get("JWT_SECRET") or _DEFAULT_JWT_SECRET
    issuer = os.environ.get("JWT_ISSUER") or _DEFAULT_JWT_ISSUER
    audience = os.environ.get("JWT_AUDIENCE") or _DEFAULT_JWT_AUDIENCE
    algorithm = os.environ.get("JWT_ALGORITHM") or _DEFAULT_JWT_ALGORITHM
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": sub,
        "name": name if name is not None else sub,
        "iat": now,
        "exp": now + ttl_seconds,
        "roles": list(roles),
        "profile_id": profile_id,
        "customer_id": customer_id,
        "mentor_id": mentor_id,
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def get_auth_token() -> str:
    """Mint a short-lived admin+mentor persona JWT for black-box tests."""
    return mint_token(
        sub=_E2E_SUBJECT,
        roles=_E2E_ROLES,
        profile_id=_E2E_PROFILE_ID,
        customer_id=_E2E_CUSTOMER_ID,
        mentor_id=_E2E_MENTOR_ID,
        name=_E2E_NAME,
    )
