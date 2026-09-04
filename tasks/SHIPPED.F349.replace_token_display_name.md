# F349 – Use token.display_name (api-utils 1.0.1)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: `F348_bump_api_utils_1_0_1`  
**Description**: After the 1.0.1 pin, replace any Flask-token `name` with `display_name` as required by [F-RA15 / issue #29](https://github.com/mentor-forge/mentorhub_mentor_api/issues/29). Leave Profile, Path, Resource, Plan, Encounter, and Event **document** `name` fields unchanged. Align JWT minting, mock token dicts, and README with the installed 1.0.1 Token contract.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `tasks/PENDING.F348.bump_api_utils_1_0_1.md` (or `SHIPPED.F348.bump_api_utils_1_0_1.md`) — pin complete; Execution Notes may list 1.0.1 Token `to_dict` keys
- `README.md` — still says `api-utils==1.0.0`
- `../mentorhub_api_utils/README.md` — JWT wire claim remains OIDC `name`; application dict key is `display_name`
- `src/routes/` — local POST/PATCH handlers call `create_flask_token()` and pass the dict through; confirm none read the token display field
- `src/services/` — token is a **dict** (`token.get("user_id")`, `token.get("roles")`, …). Confirm none still read Flask-token `"name"`. `ProfileService` matches Profile **documents** with `match={"name": mentor_name}` where `mentor_name = token.get("user_id")` — that is **not** the token display claim; do not change it.
- `test/routes/` and `test/services/` — mock token dicts typically `{user_id, roles}` (and sometimes `profile_id`). Add `display_name` only when tests or services represent `create_flask_token()` output and 1.0.1 always exposes that key.
- `test/e2e/e2e_auth.py` — already mints JWT claim `name` (OIDC). Keep minting `name` unless the installed 1.0.1 mapper **requires** a JWT `display_name` claim. Do not treat this JWT `name` as Flask-token `token["name"]`.
- `test/e2e/test_path.py` / `test/e2e/test_encounter.py` — local mint helpers; same JWT-claim rule as `e2e_auth.py`
- `docs/openapi.yaml` — `/api/config` `token` is an untyped object; domain schemas use document `name`. Do not invent a Token schema unless the live config payload is already documented as having `name`.

**Issue**: [F-RA15:bump_utils](https://github.com/mentor-forge/mentorhub_mentor_api/issues/29) — replace any use of `token.name` with `token.display_name`.

**1.0.1 Token contract** (installed package, not an assumed sibling tree):

```bash
pipenv run python -c "import inspect; from api_utils.flask_utils import token as t; print(inspect.getsource(t.Token.to_dict)); print(inspect.getsource(t.Token._map_claims))"
```

Expected mapping (confirm against the installed package): `to_dict()` / `create_flask_token()` return `display_name` from JWT `name`, then JWT `display_name`, then `""`, and **omit** application-dict `name`. Shared `create_config_routes()` will then expose that dict on `GET /api/config`.

Routes already call `create_flask_token()`, which returns a **dict**. Replacements are therefore:

| Do replace (Flask token) | Do **not** replace (domain documents / OpenAPI / JWT wire) |
| --- | --- |
| `token.name` (attribute) | Profile / Path / Resource / Plan / Encounter document `name` |
| `token["name"]` / `token.get("name")` when `token` is the Flask token dict | `token.get("user_id")` used as Profile lookup (`match={"name": ...}`) |
| Mock token dicts that include a `"name"` key for the **caller** | Event `type`, list filters, OpenAPI parameter `name:` keys |
| README pin `==1.0.0` | JWT claim `name` in `e2e_auth.py` if 1.0.1 still maps OIDC `name` → `display_name` |

If Event create copies `dict(token)` into Event `context` via the shared parent, persisted context will contain `display_name` instead of `name` after the pin. Update assertions only if tests inspect that key.

Shared `api_utils` GET factories and config routes are not copied locally; they pick up 1.0.1 automatically. Local factories only change if they read the token display field.

**MongoDB I/O**: any service edit still uses `MongoIO` only (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`). This task should not add new queries or direct PyMongo calls.

## Goals

- Zero Flask-token uses of `.name` / `["name"]` / `.get("name")` in `src/` and `test/` where the object is the caller token from `create_flask_token` / `Token`.
- Those call sites use `display_name` (attribute or dict key matching 1.0.1 `to_dict`).
- Unit-test mock tokens that intend to represent `create_flask_token()` output include `display_name` when the installed contract always exposes that key; they do not keep a misleading `"name"` key on the **token** dict.
- `test/e2e/e2e_auth.py` (and local e2e mint helpers) still satisfy 1.0.1 (`profile_id` remains required). Keep JWT `name` if that is what `_map_claims` reads; add JWT `display_name` only if the mapper requires or prefers it. Do not 401-fail e2e by omitting a claim the new Token mapper requires.
- `README.md` documents the pinned **`api-utils==1.0.1`** contract (JSON-array list GETs, `offset`/`size` headers, MongoIO) and that the Flask token dict key is `display_name`.
- `docs/openapi.yaml` is unchanged unless it documents a Flask-token `name` claim (it should not; collection `name` properties stay).
- Confirmation greps (must stay **zero** for Flask-token `name`, while document `name` hits remain):
  ```bash
  rg 'token\.name' src test
  rg 'token\[.name.\]|token\.get\(.name.\)' src test
  ```
- `GET /api/config` (shared config blueprint) returns the 1.0.1 token dict: `display_name` present, Flask-token `name` absent.

### Craftsmanship Expectations

- Token claim shape is owned by `api_utils`; this API consumes it. Do not add a local alias that accepts both `name` and `display_name`.
- Do not rename domain resource `name` fields to `display_name`.
- Prefer deleting obsolete Flask-token `"name"` usage rather than leaving dual keys on synthetic tokens.
- Do not patch `api_utils` in this repo; if 1.0.1 is missing `display_name`, F348 should have been Blocked.
- Prefer proving that a file needs no change over speculative fixture churn.

## Testing Expectations

Run all commands from this API repository root.

- **Install** (already 1.0.1 from F348; re-run if the venv is stale)
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `pipenv run install`
- **Confirmation**
  - The two `rg` commands above — **zero** hits
  - `rg 'api-utils==1\.0\.0' README.md Pipfile` — **zero** hits
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - Existing route tests still 401 without bearer; write RBAC still 403 for non-mentor/non-admin
  - Negative check: least-privileged persona JWTs still work; missing `profile_id` still 401 (do not weaken Token validation to preserve older `name` payloads)
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `docker exec` (or equivalent) `pip show api-utils` on the running Mentor API container → **1.0.1**
  - Authenticated `GET /api/config` (or the OpenAPI `/docs/openapi.yaml` smoke plus a token-bearing config curl) shows token `display_name` and no Flask-token `name`
  - `pipenv run e2e` — full suite green against the containerized API (personas in `e2e_auth.py`)

## Outputs

- `src/routes/*.py` — only if a route reads Flask-token `name`
- `src/services/*.py` — only if a service reads Flask-token `name` (not document `name` / `user_id`)
- `test/routes/*.py` — mock `create_flask_token()` return values if they include Flask-token `name` or must include `display_name`
- `test/services/*.py` — mock token dicts that represent Flask token dicts
- `test/e2e/e2e_auth.py` — JWT claims aligned with 1.0.1 `Token` mapping
- `test/e2e/test_path.py` — local mint helper, only if JWT claims must change
- `test/e2e/test_encounter.py` — local mint helper, only if JWT claims must change
- `test/e2e/test_event.py` — only if Event `context` assertions inspect token `name`
- `README.md` — pin text `1.0.1` and token dict key `display_name`
- `docs/openapi.yaml` — only if a Flask-token `name` property is actually documented

The agent must not update files outside this list. Skip files in the list that have no token-display-claim usage after the audit.

## Execution Notes

### Plan

1. Confirm installed 1.0.1 Token contract (`to_dict` / `_map_claims`): Flask-token key is `display_name` from JWT `name` then JWT `display_name` then `""`; application-dict `name` omitted; `profile_id` required. JWT minting keeps OIDC `name`.
2. Audit `src/routes/` and `src/services/`: no Flask-token `.name` / `["name"]` / `.get("name")`. `ProfileService` `match={"name": token.get("user_id")}` is a Profile **document** lookup — leave unchanged.
3. Audit mocks: route/service tokens are `{user_id, roles}` (sometimes `profile_id`); none carry a misleading Flask-token `"name"`. No service reads `display_name`, so do not churn fixtures. Event e2e does not inspect persisted context `name`.
4. Keep `e2e_auth.py` / local mint helpers minting JWT `name` (1.0.1 `_map_claims` still maps that claim). No JWT `display_name` claim required.
5. Leave `docs/openapi.yaml` unchanged (`token` is an untyped object; no Flask-token `name` property).
6. Update `README.md` only: pin `api-utils==1.0.1` and document Flask-token dict key `display_name` (list GET / `offset`/`size` / MongoIO already documented).
7. Confirmation greps, then `pipenv run test` / `lint` / `build`, then packaging (`container` / `api` / `pip show` / authenticated `GET /api/config` / `e2e`).
8. Do not change `Pipfile` version. Do not commit or push.

### Implementation

- Installed 1.0.1 confirmed: `Token.to_dict()` keys `user_id`, `display_name`, `roles`, `profile_id`, `customer_id`, `mentor_id`, `remote_ip`. `display_name` = JWT `name` or JWT `display_name` or `""`. `_map_claims` requires `profile_id`; does not add Flask-token `name`.
- `src/routes/*.py` / `src/services/*.py`: no Flask-token display-field reads. `ProfileService` `match={"name": token.get("user_id")}` left unchanged (document lookup).
- `test/routes/*.py` / `test/services/*.py`: mock tokens are `{user_id, roles}` (plus `profile_id` where needed). No token `"name"` key; no `display_name` consumer — skipped fixture churn.
- `test/e2e/e2e_auth.py`, `test_path.py`, `test_encounter.py`: JWT claim `name` kept (OIDC). No JWT `display_name` added.
- `test/e2e/test_event.py`: Event context assertions do not inspect token `name` — unchanged.
- `docs/openapi.yaml`: `/api/config` `token` is untyped object — unchanged.
- `README.md`: pin text `api-utils==1.0.1`; Flask-token key `display_name`; MongoIO note; JWT `name` → Flask-token `display_name`.
- `Pipfile` version not changed.

### Confirmation greps

- `rg 'token\.name' src test` — **zero** hits
- `rg 'token\[.name.\]|token\.get\(.name.\)' src test` — **zero** hits
- `rg 'api-utils==1\.0\.0' README.md Pipfile` — **zero** hits

### Test results

- `pipenv run test` — **156 passed**, 43 deselected
- `pipenv run lint` — pass (`50 files would be left unchanged`)
- `pipenv run build` — pass (exit 0)
- `pipenv run container` — success; image installed `api-utils==1.0.1`
- `pipenv run api` — mentor-api stack started
- `docker exec mentorhub-mentor_api-1 pip show api-utils` — **1.0.1**
- Authenticated `GET /api/config` — HTTP 200; token keys `customer_id`, `display_name` (`"Adam Admin"`), `mentor_id`, `profile_id`, `remote_ip`, `roles`, `user_id`; Flask-token `name` **absent**
- `/docs/openapi.yaml` smoke — HTTP 200
- `pipenv run e2e` — **41 passed**, 2 skipped (profile composite / properties; existing seed skips)

### Blockers

None.
