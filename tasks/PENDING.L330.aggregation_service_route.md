# L330 – Aggregation service (wrapper), GET route, and server registration

**Status**: Pending  
**Type**: Feature  
**Depends On**: L310  
**Description**: Add a thin local `AggregationService.get_aggregation_detail` that **delegates** to `api_utils.services.AggregationService` (shipped in the pinned `api-utils==0.5.1`), expose `GET /api/aggregation/{resource_id}`, and register the blueprint in `src/server.py`. The endpoint returns Resource_Aggregation metrics plus the Notes for the resource (`{ aggregation, notes }`), using the shared aggregation detail (which composes notes internally) and the OpenAPI contract from L310.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `AggregationDetail` contract added in L310
- `api_utils.services.AggregationService` — shared implementation to delegate to (`get_aggregation_detail`), shipped in `api-utils==0.5.1`
- `src/services/resource_service.py` — this repo's established thin-wrapper convention over `api_utils.services`
- `src/routes/resource_routes.py`, `src/server.py` — this repo's route/registration conventions

> **Note**: The service logic is already harvested upstream — do **not** port it from `../mentorhub_mentee_api/src/services/aggregation_service.py`. `api_utils.services.AggregationService.get_aggregation_detail(resource_id, token, breadcrumb)` already validates the `resource_id` ObjectId (→ `HTTPBadRequest`), performs the **get-or-create** of the aggregation document (zeroed counters, `rating_sum: 0`, initial `duration`, `created`/`last_saved` breadcrumbs) via `MongoIO`, composes related notes through `NoteService.list_all_notes_for_resource` (lazy import, no cycle), and returns `{ "aggregation": ..., "notes": [...] }`. The route/blueprint/server registration, however, are **mentor-local** and must be implemented here (api_utils ships services, not this repo's blueprints).

> **On L320**: The shared `get_aggregation_detail` composes notes internally via `list_all_notes_for_resource`, so L330 does **not** require L320 to function. L320's local `NoteService` wrapper is only needed if/when this API exposes its own note-read surface; keep the dependency decoupled here.

## Goals

- **New service** `src/services/aggregation_service.py`:
  - Import the shared service: `from api_utils.services import AggregationService as SharedAggregationService`.
  - Expose a local `AggregationService` class with:
    - `get_aggregation_detail(resource_id, token, breadcrumb)`:
      - Open to any authenticated user (no additional role gate).
      - **Delegate** to `SharedAggregationService.get_aggregation_detail(resource_id, token, breadcrumb)` (the shared service handles ObjectId validation → `HTTPBadRequest`, get-or-create, and note composition).
      - Return the `{ "aggregation": <ResourceAggregation>, "notes": [<Note>, ...] }` dict unchanged.
  - **No local MongoDB access**: this wrapper must not call `MongoIO` or PyMongo directly — all storage I/O is reached through the shared `api_utils.services.AggregationService`, per `_PLANNING.md`. Do **not** re-implement the get-or-create helper, `add_completion`, or `add_hit`.
- **New route** `src/routes/aggregation_routes.py` (mentor-local):
  - `GET /<resource_id>` — mint token/breadcrumb via `create_flask_token`/`create_flask_breadcrumb`, wrap with `@handle_route_exceptions`, call `AggregationService.get_aggregation_detail`, return `AggregationDetail` JSON with `200`.
- **Register blueprint** in `src/server.py` (mentor-local):
  - Import `create_aggregation_routes` and register at `url_prefix="/api/aggregation"`.
  - Add the `/api/aggregation - Aggregation domain endpoints` line to the route-registration log summary.
- **Unit tests**:
  - `test/services/test_aggregation_service.py` (new) — wrapper delegates to `api_utils.services.AggregationService.get_aggregation_detail` with the correct args and returns its `{ aggregation, notes }` result unchanged (mock the shared service); `HTTPBadRequest` from the shared service propagates. Deep get-or-create / MongoIO / note-composition behavior is **not** re-tested here — it is covered by upstream `api_utils` tests.
  - `test/routes/test_aggregation_routes.py` (new) — `GET /api/aggregation/{resource_id}` returns the composite `{ aggregation, notes }` shape; auth required.
- **E2E**:
  - `test/e2e/test_aggregation.py` (new) — `GET /api/aggregation/{resource_id}` returns `{ aggregation, notes }` and creates the aggregation when missing.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py` — delegation, composite shape, invalid-id propagation
  - `test/routes/test_aggregation_routes.py` — GET route composite shape, auth
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

- `src/services/aggregation_service.py` — **new** `get_aggregation_detail` wrapper delegating to `api_utils.services.AggregationService`
- `src/routes/aggregation_routes.py` — **new** GET route blueprint
- `src/server.py` — register aggregation blueprint at `/api/aggregation` and update route log summary
- `test/services/test_aggregation_service.py` — **new** unit tests
- `test/routes/test_aggregation_routes.py` — **new** route unit tests
- `test/e2e/test_aggregation.py` — **new** E2E tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
