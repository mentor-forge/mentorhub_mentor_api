# L160 – Resource list: adopt shared api_utils ResourceService

**Status**: Pending  
**Type**: Feature  
**Depends On**: L150_bump_api_utils_0_5_0  
**Description**: Replace the local Resource **read/list** path with the harvested shared service. Delete the local `ResourceService.get_resources` list implementation and delegate to `api_utils.services.ResourceService` (import directly, or keep a thin local wrapper that delegates). Update the `GET /api/resource` route to use header-based pagination (`offset`/`size`) plus filter query params and standardized `sort_by`/`order` query params per the shared `order_spec`. Mentor-only CRUD (`create_resource`, `update_resource`) may remain in a thin local wrapper delegating to `MongoIO`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/resource_service.py`
- `src/routes/resource_routes.py`
- `docs/openapi.yaml` (Resource paths + schemas)
- `test/services/test_resource_service.py`
- `test/routes/test_resource_routes.py`
- `test/e2e/test_resource.py`

**Shared service contract (api_utils 0.5.0)**

- Inspect `api_utils.services.ResourceService` for the exact `get_resources` signature, the `order_spec` helper, and how the offset/size pagination headers are parsed/emitted (request `offset`/`size`, standardized `sort_by`/`order` query params). Follow that contract exactly rather than inventing one; record the resolved signature in **Execution Notes**.

**Current state**

- `ResourceService.get_resources(token, breadcrumb, name=None)` is a simple full-list read sorted by `name` asc via `MongoIO.get_documents`. There is no `after_id`/`limit`/`next_cursor` cursor variant left in the service code, but `GET /api/resource` still returns an unpaginated array and `docs/openapi.yaml` still defines the `InfiniteScrollResponse` schema (removed centrally in L220).

**MongoIO rule**

- Any local wrapper that keeps Resource CRUD must route all MongoDB I/O through `MongoIO` (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`). Do not call PyMongo directly. Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- The local Resource **list** logic is removed; `GET /api/resource` is served by `api_utils.services.ResourceService` (direct import or thin delegating wrapper).
- `GET /api/resource` accepts:
  - `offset`/`size` **request headers** for pagination (no `after_id`/`limit` cursor params).
  - Filter query params (at minimum `name`, partial/case-insensitive) as supported by the shared service.
  - Standardized `sort_by`/`order` query params validated per the shared `order_spec`.
- Mentor-only `create_resource` / `update_resource` remain available (local thin wrapper delegating to `MongoIO`) with unchanged behavior and RBAC.
- Response is a plain array (no `{items, has_more, next_cursor}` envelope); pagination metadata is conveyed via response headers per the shared contract.
- Unit and E2E tests for Resource pass.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev` (separate terminal / background)
  - `pipenv run e2e`
  - Manual check: `curl -sD - "http://localhost:8391/api/resource?sort_by=name&order=asc" -H "Authorization: Bearer $TOKEN" -H "offset: 0" -H "size: 10"` returns an array and pagination headers.
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/resource_service.py` — remove local list logic; delegate list reads to `api_utils.services.ResourceService`; retain mentor-only CRUD as a thin `MongoIO` wrapper
- `src/routes/resource_routes.py` — `GET /api/resource` uses offset/size headers + filter + `sort_by`/`order` query params
- `docs/openapi.yaml` — Resource `GET /api/resource` operation: replace cursor params with header pagination + `sort_by`/`order` query params (schema cleanup of `InfiniteScrollResponse` is centralized in L220)
- `test/services/test_resource_service.py` — update for delegated list + retained CRUD
- `test/routes/test_resource_routes.py` — update for header pagination + query params
- `test/e2e/test_resource.py` — update expectations (array response + pagination headers)

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
