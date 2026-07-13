# L190 – Plan list: add offset/size header pagination

**Status**: Pending  
**Type**: Feature  
**Depends On**: L180_path_list_align_api_utils_service  
**Description**: Add `offset`/`size` header pagination to `PlanService.get_plans`, which today returns the full sorted list with no parameters. Optionally support a `name` "contains" filter. Plan remains a **mentor-only local domain** (do not delegate to a shared service); this task just adopts the standardized header-pagination + `sort_by`/`order` conventions so the Plan list is consistent with the migrated list endpoints.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/plan_service.py`
- `src/routes/plan_routes.py`
- `docs/openapi.yaml` (Plan paths + schemas)
- `test/services/test_plan_service.py`
- `test/e2e/test_plan.py`

**Pagination/order convention (api_utils 0.5.0)**

- Reuse the same offset/size header parsing and `sort_by`/`order` `order_spec` helpers adopted in L160–L180 so Plan behaves consistently. Inspect `api_utils.services` / shared helpers for the exact helper names and header contract; record what you used in **Execution Notes**.

**Current state**

- `PlanService.get_plans(token, breadcrumb)` returns **all** plans sorted by `name` asc (explicitly documented today as "no search, pagination, or infinite scroll"). `GET /api/plan` takes no query params. `docs/openapi.yaml` line ~366 documents this. Update the docstrings/descriptions that assert "no pagination" to reflect the new behavior.

**MongoIO rule**

- Plan stays local: route all MongoDB I/O through `MongoIO` (no direct PyMongo). Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- `PlanService.get_plans` accepts pagination via `offset`/`size` (default page when headers absent) while still sorting by `name` asc by default.
- Standardized `sort_by`/`order` query params are honored per the shared order spec.
- Optional `name` "contains" (partial, case-insensitive) filter is supported.
- `GET /api/plan` route parses offset/size headers + query params and emits pagination response headers per the shared contract.
- Docstrings/OpenAPI descriptions no longer claim the list is non-paginated.
- Unit and E2E tests for Plan pass.

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
  - Manual check: `curl -sD - "http://localhost:8391/api/plan?name=intro&sort_by=name&order=asc" -H "Authorization: Bearer $TOKEN" -H "offset: 0" -H "size: 10"`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/plan_service.py` — `get_plans` gains offset/size pagination, `sort_by`/`order`, optional `name` contains filter; update docstring
- `src/routes/plan_routes.py` — `GET /api/plan` parses offset/size headers + query params; emits pagination headers
- `docs/openapi.yaml` — Plan `GET /api/plan` operation: document header pagination + `sort_by`/`order` + optional `name` filter; remove the "no pagination" wording
- `test/services/test_plan_service.py` — cover pagination, ordering, and name filter
- `test/e2e/test_plan.py` — update expectations (pagination headers + optional filter)

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
