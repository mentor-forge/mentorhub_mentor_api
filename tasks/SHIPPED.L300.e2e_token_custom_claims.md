# L300 – E2E tokens: add required profile_id and custom claims (customer_id, mentor_id)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: The shared Developer-Edition IdP now mints JWTs with custom claims `profile_id`, `customer_id`, and `mentor_id` in addition to `roles` (see `../mentorhub/login.html` / `../mentorhub/welcome-auth.js`). Under the new contract `profile_id` is **required** (as is `roles`), so every E2E test that mints a token without `profile_id` will produce an invalid token once the API enforces the contract. Update the E2E token-minting helpers so all minted tokens carry the new claim set, with `profile_id` (and `roles`) always present. This is a **test-only** change: no `src/`, route, service, or `docs/openapi.yaml` changes are expected or permitted.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`

Token-contract inputs (source of truth for the new claim set):

- `../mentorhub/login.html` — Developer sign-in page description.
- `../mentorhub/welcome-auth.js` — the local IdP minting logic. The signed payload is:
  `{ iss, aud, sub, name, iat, exp, roles, profile_id, customer_id, mentor_id }`. It also documents the fixed HS256 secret (`local-dev-jwt-secret-fixed`), issuer (`dev-idp`), and audience (`dev-api`) — the same defaults the E2E helpers already use — plus the canonical per-persona claim values (`PROFILES`).
- `../mentorhub_api_utils/api_utils/flask_utils/token.py` — how the API decodes/validates the JWT (`iss`/`aud`/`exp`/`alg`) and maps claims. Use this to confirm which claims the API validates on decode so the minted tokens remain acceptable.
- `../mentorhub_mongodb_api/configurator/test_data/Profile.0.1.0.0.json` — seeded Profile documents, to pick `profile_id` values that are real and consistent with the personas in `welcome-auth.js`.

E2E files that mint tokens (the only files this task changes):

- `test/e2e/e2e_auth.py` — central `get_auth_token()`; today mints `{ iss, aud, sub, iat, exp, roles }` with `sub="adam"` and `roles=("admin", "mentor")`. Missing `profile_id`/`customer_id`/`mentor_id`/`name`.
- `test/e2e/test_path.py` — local `_mint_token(roles)` (persona used for the mentee-role PATCH denial case).
- `test/e2e/test_encounter.py` — local `_mentor_only_token(subject=...)` (mentor-only persona used for the non-owner PATCH denial case).

Consumers to keep green (do not edit; verify behavior is preserved): `test/e2e/test_profile.py`, `test/e2e/test_resource.py`, `test/e2e/test_event.py`, `test/e2e/test_plan.py`, `test/e2e/test_mentee.py` all obtain their token via `e2e_auth.get_auth_token()`.

## Goals

- Every JWT minted by the E2E suite includes the new custom claims: `profile_id` (**required**), `customer_id`, and `mentor_id`, alongside the existing `roles` — matching the payload shape produced by `welcome-auth.js`.
- `test/e2e/e2e_auth.py::get_auth_token` mints the **default persona** token with:
  - `profile_id` set to a real seeded Profile id, and `roles` that still include **both** `admin` and `mentor` (so role-gated reads and the owner-or-admin PATCH bypass in the Encounter/Path tests keep passing exactly as today). Align the persona (`sub`/`name`/`profile_id`/`customer_id`/`mentor_id`) to one of the `welcome-auth.js` personas that carries admin+mentor (e.g. `mike` or `sam`), or retain the current `sub` and simply add a valid `profile_id` — whichever keeps the existing Profile-dashboard tests behaving the same (they resolve the mentor by `Profile.name`, and already `skip` when the dashboard is empty). Record the chosen persona and rationale in **Execution Notes**.
- `test/e2e/test_path.py::_mint_token` and `test/e2e/test_encounter.py::_mentor_only_token` include `profile_id` (and `customer_id`/`mentor_id`) so their tokens are valid, **without** changing the outcome of the RBAC denial cases:
  - The mentee-role Path PATCH case still returns `403`.
  - The non-owner-mentor Encounter PATCH case still returns `403` — i.e. the chosen `profile_id` must **not** equal the `mentor_id` of the encounter created in that test (`507f1f77bcf86cd7994390ff`), so ownership still fails.
- Prefer consolidating the claim set in one place: consider adding a small shared helper/constant in `test/e2e/e2e_auth.py` (e.g. a `mint_token(sub, roles, profile_id, customer_id="", mentor_id="", name=None)` function) and having the two local minters call it, to avoid three divergent payload builders. Keep the environment-variable overrides (`JWT_SECRET`/`JWT_ISSUER`/`JWT_AUDIENCE`/`JWT_ALGORITHM`) that the helpers use today.
- No changes outside `test/e2e/`. `src/`, routes, services, and `docs/openapi.yaml` are untouched.
- Full unit suite still passes and the E2E suite passes against a running API.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests** (must remain green; this task does not change unit tests)
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev` (separate terminal / background)
  - `pipenv run e2e`
  - Confirm all previously passing/`skip`ping E2E cases keep the same outcome; in particular the Path mentee-role PATCH and Encounter non-owner PATCH cases still return `403`.
  - Manual token sanity check (optional): decode a minted token and confirm `profile_id`, `customer_id`, `mentor_id`, and `roles` are present, e.g.
    `pipenv run python -c "from test.e2e.e2e_auth import get_auth_token; import jwt; print(jwt.decode(get_auth_token(), 'local-dev-jwt-secret-fixed', algorithms=['HS256'], audience='dev-api', issuer='dev-idp'))"`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `test/e2e/e2e_auth.py` — `get_auth_token` mints the full claim set (`profile_id` required + `customer_id`/`mentor_id`/`name`) for an admin+mentor persona aligned to `welcome-auth.js`; optionally add a shared `mint_token(...)` helper.
- `test/e2e/test_path.py` — `_mint_token` includes the new claims (delegating to the shared helper if added); mentee-role PATCH denial (`403`) preserved.
- `test/e2e/test_encounter.py` — `_mentor_only_token` includes the new claims (delegating to the shared helper if added); non-owner-mentor PATCH denial (`403`) preserved (chosen `profile_id` must not own the test encounter).

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
