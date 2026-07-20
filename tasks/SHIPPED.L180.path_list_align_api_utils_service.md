# L180 – Path list: align with shared api_utils PathService

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L170_event_list_adopt_api_utils_service  
**Description**: Align the Path **list** path with the harvested `api_utils.services.PathService` (header pagination + `name` filter + standardized `sort_by`/`order`). Remove the duplicate local `path_service.py` list logic. Path CRUD (`create_path`, `update_path`, `get_path`) stays local unless/until Path CRUD is separately harvested; if it is, delegate accordingly and note it.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/path_service.py`
- `src/routes/path_routes.py`
- `docs/openapi.yaml` (Path paths + schemas)
- `test/services/test_path_service.py`
- `test/routes/test_path_routes.py`
- `test/e2e/test_path.py`

**Shared service contract (api_utils 0.5.0)**

- Inspect `api_utils.services.PathService` for the `get_paths` signature, order spec, `name` filter behavior, and offset/size header handling. Follow that contract; record the resolved signature in **Execution Notes**.

**Current state**

- `PathService.get_paths(token, breadcrumb, name=None)` is a full-list read with optional case-insensitive `name` regex, sorted by `name` asc. `update_path` enforces mentor/admin RBAC via `Config` role constants; `create_path`/`get_path` are authenticated-only. Keep CRUD local for now.

**MongoIO rule**

- Retained local Path CRUD must route all MongoDB I/O through `MongoIO` (no direct PyMongo). Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- The duplicate local Path **list** logic is removed; `GET /api/path` is served by (or delegates to) `api_utils.services.PathService`.
- `GET /api/path` accepts `offset`/`size` request headers, a `name` filter query param, and standardized `sort_by`/`order` query params per the shared order spec.
- Path CRUD (`create_path`, `update_path`, `get_path`) retains current behavior and RBAC (mentor/admin required for update).
- Response is a plain array; pagination metadata via response headers per the shared contract.
- Unit and E2E tests for Path pass.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev`
  - `pipenv run e2e`
  - Manual check: `curl -sD - "http://localhost:8391/api/path?name=onboard&sort_by=name&order=asc" -H "Authorization: Bearer $TOKEN" -H "offset: 0" -H "size: 10"`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/path_service.py` — remove duplicate local list logic; delegate list reads to `api_utils.services.PathService`; retain local CRUD
- `src/routes/path_routes.py` — `GET /api/path` uses offset/size headers + `name` filter + `sort_by`/`order`
- `docs/openapi.yaml` — Path `GET /api/path` operation: header pagination + filter/order query params (central schema cleanup in L220)
- `test/services/test_path_service.py` — update for delegated list + retained CRUD
- `test/routes/test_path_routes.py` — update for header pagination + filter
- `test/e2e/test_path.py` — update expectations (array response + pagination headers)

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
