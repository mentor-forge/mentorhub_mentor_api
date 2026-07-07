# L120 – Get Paths returns all documents (remove pagination / infinite scroll)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Change `GET /api/path` so it always returns every matching Path document as a plain JSON array, and drop the infinite-scroll contract entirely. Remove the `after_id`, `limit`, `sort_by`, and `order` query parameters and the `{items, limit, has_more, next_cursor}` envelope from the route, the `PathService.get_paths` service, and the OpenAPI spec. The optional `?name=` filter is retained. Sorting becomes a fixed server-side sort by `name` ascending (no client-selectable sort), consistent with a full-list read.

## Context

Always read these files before starting work:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml`
- `../mentorhub_api_utils/README.md`

**Prerequisites (local infra & schema source of truth)**

Before starting work, start the backing database and verify the schema source of truth:

- Start the backing database locally: `pipenv run db`
- Verify the schema source of truth (trailing slash required):
  `curl http://localhost:8383/api/configurations/json_schema/Path.yaml/latest/`

Additional inputs:

- `src/routes/path_routes.py` — the `get_paths` view bound to `GET ''`; currently reads `name`, `after_id`, `limit`, `sort_by`, `order` and returns the scroll envelope. Update the docstring that enumerates parameters.
- `src/services/path_service.py` — `get_paths` currently calls `execute_infinite_scroll_query(...)` with `ALLOWED_SORT_FIELDS`. Replace with a direct `MongoIO.get_documents(...)` full-collection read (see the `EncounterService.get_encounters_for_mentee` pattern using `mongo.get_documents(collection, match=..., sort_by=[...])`). Remove the now-unused `execute_infinite_scroll_query` import and `ALLOWED_SORT_FIELDS` constant only if they are not referenced elsewhere in the file.
- `docs/openapi.yaml` — the `GET /api/path` operation (`operationId: getPaths`), its query parameters, and its `200` response schema (the `items/limit/has_more/next_cursor` object).
- `test/routes/test_path_routes.py`, `test/services/test_path_service.py`, `test/e2e/test_path.py` — remove/adjust pagination and scroll assertions; assert a plain array response.

## Goals

- `GET /api/path` returns a JSON array of Path documents (all matching documents, no batching). The optional `?name=` filter still narrows results (partial, case-insensitive, unchanged semantics).
- The `after_id`, `limit`, `sort_by`, and `order` query parameters are removed from the route, service signature, and OpenAPI operation. Results are sorted by `name` ascending server-side.
- `PathService.get_paths` no longer uses `execute_infinite_scroll_query`; it reads the full (optionally name-filtered) collection via `MongoIO.get_documents(...)` and returns the list. Unused `execute_infinite_scroll_query` import and `ALLOWED_SORT_FIELDS` constant are deleted if no longer referenced.
- `docs/openapi.yaml` `getPaths` `200` schema is `type: array` of `#/components/schemas/Path` (envelope removed); the four pagination/scroll query parameters are removed; description updated to "Return all Path documents".
- Existing `_check_permission(token, 'read')` behavior is preserved (no RBAC change in this task).
- Unit tests pass and reflect the array response.

## Testing Expectations

Run all commands from the API repository root.

- **Unit tests** — `pipenv run test`. Update `test/services/test_path_service.py` and `test/routes/test_path_routes.py`:
  - Remove tests asserting the `{items, limit, has_more, next_cursor}` envelope, `after_id`/`limit`/`sort_by`/`order` handling, and `HTTPBadRequest` for invalid scroll parameters.
  - Add/adjust tests asserting `get_paths` returns a list of all documents, that `?name=` still filters, and the route returns a JSON array with `200`.
- **Lint / build** — `pipenv run lint`, `pipenv run build` (no unused-import/lint regressions from the removed scroll helper).
- **Dev / E2E (when infra available)** — `pipenv run db`, `pipenv run dev`, `pipenv run e2e`; update `test/e2e/test_path.py` to assert `GET /api/path` returns an array (drop scroll-cursor cases). 
- **Packaging verification** — `pipenv run container`, `pipenv run api`, then `curl -s http://localhost:8391/docs/openapi.yaml | head` to confirm the updated spec is served.

## Outputs

Paths are relative to the API repository root.

- `src/routes/path_routes.py` — simplify `get_paths` to read only `name`, return the array; update the docstring.
- `src/services/path_service.py` — replace scroll query with a full `get_documents` read; remove unused import/constant if unreferenced.
- `docs/openapi.yaml` — `getPaths` array response + removed pagination/scroll parameters and description update.
- `test/routes/test_path_routes.py` — array-response route tests; remove scroll tests.
- `test/services/test_path_service.py` — full-list service tests; remove scroll tests.
- `test/e2e/test_path.py` — array-response e2e; remove scroll-cursor cases.

The agent must not update files outside this list.

## Execution Notes

### Changes

- `src/services/path_service.py` — `get_paths(token, breadcrumb, name=None)` now reads the full collection via `MongoIO.get_documents(PATH_COLLECTION_NAME, match=..., sort_by=[("name", ASCENDING)])` and returns the list. Optional `name` applies a case-insensitive partial match (`{"$regex": name, "$options": "i"}`). Removed the `execute_infinite_scroll_query` import, the `ALLOWED_SORT_FIELDS` constant, and the now-unused `HTTPBadRequest` import; added `from pymongo import ASCENDING`.
- `src/routes/path_routes.py` — `GET /api/path` view now reads only `name` and returns `jsonify(list)`; docstring updated. The route path is unchanged (`/api/path`, registered in `server.py`).
- `docs/openapi.yaml` — `getPaths` now documents "Return all Path documents, sorted by name ascending"; removed the `after_id`/`limit`/`sort_by`/`order` query params and the `400` response; `200` schema is now `type: array` of `#/components/schemas/Path`.
- Tests — `test/services/test_path_service.py`: replaced the six scroll/pagination tests with `test_get_paths_returns_all` and `test_get_paths_name_filter`, and repointed the exception test at `get_documents`. `test/routes/test_path_routes.py`: both list tests now assert a JSON array and the `name=`-only call signature. `test/e2e/test_path.py`: list e2e cases now assert a JSON array.

### Test results

- `pipenv run test` → **191 passed, 30 deselected** (e2e).
- `pipenv run build` → exit 0.
- `pipenv run black` → the 5 edited files reformatted and black-clean; repo-wide pre-existing lint debt left untouched.
- E2E / container (`pipenv run db`/`dev`/`e2e`/`api`) deferred — container infra (`mh`) not available in this environment; updated cases are marked `@pytest.mark.e2e`.

### Note

The Flask route is `/api/path` (singular, per `server.py` and the OpenAPI paths). The task prose was corrected from `/api/paths` to `/api/path`; no route rename was performed (not in Outputs) — only the response shape and query params changed.
