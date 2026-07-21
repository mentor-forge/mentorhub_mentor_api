# L330 – Aggregation service, GET route, and server registration

**Status**: Pending  
**Type**: Feature  
**Depends On**: L310, L320  
**Description**: Implement `AggregationService.get_aggregation_detail`, expose `GET /api/aggregation/{resource_id}`, and register the blueprint in `src/server.py`. The endpoint returns Resource_Aggregation metrics plus the Notes for the resource (`{ aggregation, notes }`), using the read-only note lookup from L320 and the OpenAPI contract from L310.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `AggregationDetail` contract added in L310
- `src/services/note_service.py` — read-only note lookup added in L320 (`get_notes_for_resource`)
- `api_utils.Config` — `RESOURCE_AGGREGATION_COLLECTION_NAME` (default `"Resource_Aggregation"`)
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `MongoIO` helpers (`get_document`, `get_documents`, `create_document`)

Reference implementation to port from (already shipped in the mentee API):

- `../mentorhub_mentee_api/src/services/aggregation_service.py` — source of `get_aggregation_detail` and the get-or-create helper (port the read/detail path; `add_completion`/`add_hit` are NOT required for this task)
- `../mentorhub_mentee_api/src/routes/aggregation_routes.py` — source of the `GET /<resource_id>` route
- `../mentorhub_mentee_api/src/server.py` — blueprint registration pattern at `/api/aggregation`
- `../mentorhub_mentee_api/tasks/SHIPPED.L050.aggregation_service_and_route.md` — original task describing the contract
- `src/routes/resource_routes.py`, `src/server.py` — this repo's route/registration conventions

## Goals

- **New service** `src/services/aggregation_service.py`:
  - `get_aggregation_detail(resource_id, token, breadcrumb)`:
    - Open to any authenticated user (no additional role gate).
    - Validate `resource_id` is a valid MongoDB `ObjectId`; raise `HTTPBadRequest` otherwise.
    - Look up aggregation by id on `config.RESOURCE_AGGREGATION_COLLECTION_NAME`; if none exists, **create** a new document with zeroed counters (`note_count`, `completions`, `hits`, `rating_count`), `rating_sum: 0`, initial `duration`, and `created`/`last_saved` breadcrumbs, then re-read it.
    - Fetch related notes via **service-to-service** call to `NoteService.get_notes_for_resource` (import inside the method to avoid circular imports).
    - Return `{ "aggregation": <ResourceAggregation>, "notes": [<Note>, ...] }`.
  - **MongoIO-only**: all MongoDB I/O goes through `MongoIO`, per `_PLANNING.md`. Scope is read/get-or-create only — do **not** port `add_completion` or `add_hit` in this task.
- **New route** `src/routes/aggregation_routes.py`:
  - `GET /<resource_id>` — mint token/breadcrumb via `create_flask_token`/`create_flask_breadcrumb`, wrap with `@handle_route_exceptions`, call `AggregationService.get_aggregation_detail`, return `AggregationDetail` JSON with `200`.
- **Register blueprint** in `src/server.py`:
  - Import `create_aggregation_routes` and register at `url_prefix="/api/aggregation"`.
  - Add the `/api/aggregation - Aggregation domain endpoints` line to the route-registration log summary.
- **Unit tests**:
  - `test/services/test_aggregation_service.py` (new) — get-or-create detail, notes included via mocked `NoteService`, invalid `resource_id` → `400`.
  - `test/routes/test_aggregation_routes.py` (new) — `GET /api/aggregation/{resource_id}` returns composite `{ aggregation, notes }` shape; auth required.
- **E2E**:
  - `test/e2e/test_aggregation.py` (new) — `GET /api/aggregation/{resource_id}` returns `{ aggregation, notes }` and creates the aggregation when missing.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py` — detail, get-or-create, notes, RBAC/validation
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

- `src/services/aggregation_service.py` — **new** `get_aggregation_detail` + get-or-create helper
- `src/routes/aggregation_routes.py` — **new** GET route blueprint
- `src/server.py` — register aggregation blueprint at `/api/aggregation` and update route log summary
- `test/services/test_aggregation_service.py` — **new** unit tests
- `test/routes/test_aggregation_routes.py` — **new** route unit tests
- `test/e2e/test_aggregation.py` — **new** E2E tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
