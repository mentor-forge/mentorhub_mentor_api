# L330 – Aggregation GET route (route → `api_utils.services`) and server registration

**Status**: Complete  
**Type**: Feature  
**Depends On**: L310  
**Description**: Expose `GET /api/aggregation/{resource_id}`, implemented by calling `api_utils.services.AggregationService.get_aggregation_detail` (shipped in the pinned `api-utils==0.5.1`) **directly from the route layer** — no local `src/services/aggregation_service.py` wrapper. The shared service is a pure pass-through with no mentor-local behavior, so per this repo's convention (see `_PLANNING.md` → *Shared services*) fully-upstream domains are adopted directly in the route rather than behind a thin delegating wrapper. The route/blueprint/server registration remain **mentor-local** (api_utils ships services, not this repo's blueprints). The endpoint returns Resource_Aggregation metrics plus the Notes for the resource (`{ aggregation, notes }`), using the shared aggregation detail (which composes notes internally) and the OpenAPI contract from L310.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `_PLANNING.md` — *Shared services (`api_utils.services`)* convention (direct route adoption for fully-upstream domains)
- `docs/openapi.yaml` — `AggregationDetail` contract added in L310
- `api_utils.services.AggregationService` — shared implementation the route consumes directly (`get_aggregation_detail`), shipped in `api-utils==0.5.1`
- `src/routes/resource_routes.py`, `src/server.py` — this repo's route/registration conventions

> **Note**: The service logic is already harvested upstream — do **not** port it from `../mentorhub_mentee_api/src/services/aggregation_service.py`, and do **not** add a local wrapper around it. `api_utils.services.AggregationService.get_aggregation_detail(resource_id, token, breadcrumb)` already validates the `resource_id` ObjectId (→ `HTTPBadRequest`), performs the **get-or-create** of the aggregation document (zeroed counters, `rating_sum: 0`, initial `duration`, `created`/`last_saved` breadcrumbs) via `MongoIO`, composes related notes through `NoteService.list_all_notes_for_resource` (lazy import, no cycle), and returns `{ "aggregation": ..., "notes": [...] }`. The route/blueprint/server registration, however, are **mentor-local** and must be implemented here.

## Goals

- **New route** `src/routes/aggregation_routes.py` (mentor-local, no local service):
  - Import the shared service directly: `from api_utils.services import AggregationService`.
  - `GET /<resource_id>` — mint token/breadcrumb via `create_flask_token`/`create_flask_breadcrumb`, wrap with `@handle_route_exceptions`, call `AggregationService.get_aggregation_detail(resource_id, token, breadcrumb)` **directly**, and return the `{ "aggregation": <ResourceAggregation>, "notes": [<Note>, ...] }` dict as `AggregationDetail` JSON with `200`.
  - Open to any authenticated user (no additional role gate; auth is enforced by `create_flask_token`).
  - **No local service module**: do **not** create `src/services/aggregation_service.py`. The shared service is pure pass-through, so a delegating wrapper would be dead indirection (per `_PLANNING.md` → *Shared services*).
  - **No local MongoDB access**: the route must not call `MongoIO` or PyMongo directly — all storage I/O is reached through `api_utils.services.AggregationService`.
- **Register blueprint** in `src/server.py` (mentor-local):
  - Import `create_aggregation_routes` and register at `url_prefix="/api/aggregation"` (keep the blueprint registrations in alphabetical order).
  - Add the `/api/aggregation - Aggregation domain endpoints` line to the route-registration log summary (alphabetical).
- **Unit tests**:
  - `test/routes/test_aggregation_routes.py` (new) — `GET /api/aggregation/{resource_id}` returns the composite `{ aggregation, notes }` shape (mock `api_utils.services.AggregationService.get_aggregation_detail` at the route boundary); auth required; `HTTPBadRequest` from the shared service surfaces as `400`. Deep get-or-create / MongoIO / note-composition behavior is **not** re-tested here — it is covered by upstream `api_utils` tests.
  - Do **not** add `test/services/test_aggregation_service.py` — there is no local service to test.
- **E2E**:
  - `test/e2e/test_aggregation.py` (new) — `GET /api/aggregation/{resource_id}` returns `{ aggregation, notes }` and creates the aggregation when missing.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_aggregation_routes.py` — GET route composite shape, auth, invalid-id → 400
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e` — includes `test/e2e/test_aggregation.py`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API
  - `curl -s http://localhost:8391/docs/openapi.yaml | head` — confirm the endpoint is served

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/aggregation_routes.py` — **new** GET route blueprint that calls `api_utils.services.AggregationService.get_aggregation_detail` directly
- `src/server.py` — register aggregation blueprint at `/api/aggregation` and update route log summary
- `test/routes/test_aggregation_routes.py` — **new** route unit tests
- `test/e2e/test_aggregation.py` — **new** E2E tests

The agent must not update files outside this list.

## Execution Notes

1. Created `src/routes/aggregation_routes.py` exposing `GET /<resource_id>` calling `api_utils.services.AggregationService.get_aggregation_detail` directly with exception handler wrapper and auth/breadcrumb helpers.
2. Registered blueprint in `src/server.py` at `/api/aggregation` and updated route registration logging.
3. Created unit tests in `test/routes/test_aggregation_routes.py` verifying 200 composite response, 401 on unauthorized, and 400 on bad request.
4. Created E2E test in `test/e2e/test_aggregation.py`.
5. Passed all formatting, linting, build, and unit tests (`pipenv run format && pipenv run lint && pipenv run build && pipenv run test`).

