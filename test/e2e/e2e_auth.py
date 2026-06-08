"""E2E Bearer JWT aligned with the umbrella welcome page (``index.html``) persona tokens (TOKEN_ADAM).

Uses ``JWT_SECRET``, ``JWT_ISSUER``, ``JWT_AUDIENCE``, and ``JWT_ALGORITHM`` from the
environment when set (``pipenv run e2e`` exports the Developer Edition defaults). Override
those variables to match a non-default API stack (same values the container / compose uses).
"""

from __future__ import annotations

import os
import time

import jwt

# Defaults match index.html static welcome tokens (HS256, iss dev-idp, aud dev-api) and Pipfile dev/e2e.
_DEFAULT_JWT_SECRET = "local-dev-jwt-secret-fixed"
_DEFAULT_JWT_ISSUER = "dev-idp"
_DEFAULT_JWT_AUDIENCE = "dev-api"
_DEFAULT_JWT_ALGORITHM = "HS256"

_E2E_SUBJECT = "adam"
_E2E_ROLES = ("admin",)


def get_auth_token() -> str:
    """Mint a short-lived admin persona JWT for black-box tests."""
    secret = os.environ.get("JWT_SECRET") or _DEFAULT_JWT_SECRET
    issuer = os.environ.get("JWT_ISSUER") or _DEFAULT_JWT_ISSUER
    audience = os.environ.get("JWT_AUDIENCE") or _DEFAULT_JWT_AUDIENCE
    algorithm = os.environ.get("JWT_ALGORITHM") or _DEFAULT_JWT_ALGORITHM
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": _E2E_SUBJECT,
        "iat": now,
        "exp": now + 10 * 365 * 24 * 60 * 60,
        "roles": list(_E2E_ROLES),
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token

