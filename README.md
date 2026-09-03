# Mentor Hub — Mentor API

## Prerequisites
- Mentor Hub [Developers Edition](https://github.com/mentor-forge/mentorhub/blob/main/CONTRIBUTING.md)
- Developer [API Standard Prerequisites](https://github.com/mentor-forge/mentorhub/blob/main/DeveloperEdition/standards/api_standards.md)
- Dependency: `api-utils==1.0.1` (pinned in `Pipfile` via CodeArtifact)
- Flask token dict key is `display_name` (JWT wire claim remains OIDC `name`). `create_flask_token()` / `GET /api/config` `token` expose `display_name` and omit application-dict `name`.

## Ownership

| Layer | Owns |
|-------|------|
| `api_utils` | Shared GET/list, outbound visibility (`build_outbound_match` / `require_outbound`), shared route factories, Mongo/Flask utilities, Event create |
| This repo (Mentor API) | Domain subclasses, control POST/PATCH (Resource/Path/Plan/Encounter), Mentee create-if-missing + update, Event by-id, Mentor Dashboard / ProfileDetail / Properties enrich, inbound write RBAC |
| OpenAPI (`docs/openapi.yaml`) | External HTTP contract (source of truth for SPA clients) |
| Mentee API | Aggregation hit/completion writes; Mentor only **consumes** aggregation |

Do **not** reimplement shared list/get outbound filters locally. Do **not** pass `api_utils.services.*` directly into `create_*_get_routes` — always pass the local subclass so domain overrides dispatch correctly.

## Architecture & Subclassing

- **Services (`src/services/`)**: Subclass the shared domain services from `api_utils.services` (Resource, Path, Plan, Encounter, Mentee, Event, Journey, Profile, Aggregation). Subclasses implement mentor-local write CRUD (POST/PATCH), Mentor Dashboard aggregation, composite views, and inbound write RBAC (`ROLE_MENTOR` / `ROLE_ADMIN`). Admin is root on writes. All MongoDB I/O goes through `MongoIO`.
- **Routes (`src/routes/`)**: Mount shared consume GET endpoints using factory functions from `api_utils.routes.shared_get_routes` passing the **local** service subclasses. Local write operations (POST, PATCH) and specialized endpoints (e.g. Properties hub, Event by-id) are mounted on the returned blueprints.
- **List GET Contract**: Plain JSON **array** body (status `200`). Pagination via `offset` / `size` **request** headers only (defaults `0` / `20`). **No** `X-Pagination-*` response headers and **no** cursor envelope.
- **Outbound visibility**: Shared GET/list hides archived / out-of-scope documents from non-admin callers. Missing and hidden both surface as **404** (never 403) so ids are not leaked. Aggregation returns **`null`** (200) when the parent Resource is missing/hidden or no aggregation row exists — it does not create documents.
- **Mentee create-if-missing**: Creates a default notes document only when none exists. An existing but hidden/archived row must remain 404 (no duplicate create).
- **Prohibited legacy patterns**: Composition wrappers that re-call `SharedXService.get_*`; local list handlers duplicating `parse_list_request`; pagination response headers; binding shared service classes into route factories.

## Developer Commands

```bash
## Install dependencies (run `mh` first for CodeArtifact auth)
pipenv run install

# start backing db container 
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests 
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8391
pipenv run dev

## run E2E tests (assumes running API at localhost:8391)
pipenv run e2e

## run tests with coverage report
pipenv run coverage

## build application (pre-compiles Python code)
pipenv run build

## build container 
pipenv run container

## Run the backing database and api containers
pipenv run api

## Run the full microservice (db+api+spa)
pipenv run service

## format code
pipenv run format

## lint code
pipenv run lint
```

## Project Structure

- `src/` - Main package containing:
  - `server.py` - API entrypoint
  - `routes/` - HTTP request/response handlers (wired via shared GET factories and local blueprints)
  - `services/` - Business logic and RBAC (subclassing `api_utils.services`)

- `test/` - Test suite with matching directory structure:
  - `routes/` - Route unit tests
  - `services/` - Service unit tests
  - `e2e/` - End-to-end tests flagged with `@pytest.mark.e2e` (include adversarial boundary cases in `test_boundaries.py`)

## API Endpoints

see the [Open API Specifications](./docs/openapi.yaml) for details on the API

For E2E, mint a Bearer token via `test/e2e/e2e_auth.py` (`get_auth_token()` / `mint_token(...)`) with `pipenv run dev` (matching `JWT_SECRET`). Personas mint the OIDC JWT `name` claim; api-utils 1.0.1 maps that into Flask-token `display_name`. Prefer least-privilege personas for outbound RBAC cases; the default token is admin+mentor for privileged write paths.

### Simple Curl Commands:
```bash
# Bearer token for local dev (same JWT settings as pipenv run dev / e2e):
export TOKEN="$(PYTHONPATH=. pipenv run python -c 'from test.e2e.e2e_auth import get_auth_token; print(get_auth_token())')"

# Get the API Configuration
curl http://localhost:8391/api/config \
  -H "Authorization: Bearer $TOKEN"

```
