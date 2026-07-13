# L230 – Tests: rewrite pagination expectations across suites

**Status**: Pending  
**Type**: Feature  
**Depends On**: L220_openapi_pagination_sweep  
**Description**: Rewrite the E2E and service tests that still assume the cursor/infinite-scroll envelope `{items, has_more, next_cursor}` so they assert the new header-based pagination contract (plain array bodies + `offset`/`size` request headers + pagination response headers + `sort_by`/`order` and filter query params). Primary targets are `test/e2e/test_resource.py` and `test/e2e/test_event.py`, plus any service tests carrying the old envelope expectations.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `docs/openapi.yaml` (post-L220 contract)
- `test/e2e/test_resource.py`
- `test/e2e/test_event.py`
- `test/e2e/e2e_auth.py`
- `test/services/test_resource_service.py`
- `test/services/test_event_service.py`
- `test/services/test_path_service.py`
- `test/services/test_plan_service.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_profile_routes.py`

**Current state**

- Local list logic was refactored to full-list reads in earlier work, but tests and fixtures may still reference the old `{items, has_more, next_cursor}` envelope or cursor params. Search the test tree for `items`, `has_more`, `next_cursor`, `after_id`, and `limit` and reconcile each hit against the new contract. (`test/routes/test_profile_routes.py` currently references `items` — confirm whether that is dashboard `progress` data or a stale pagination envelope.)
- The migrations in L160–L200 are the source of truth for each endpoint's request/response contract; tests must match the headers and query params actually implemented there.

**Pagination contract to assert**

- Request pagination via `offset`/`size` **headers**; ordering via `sort_by`/`order` **query params** (per `order_spec` / `EVENT_LIST_ORDER`); filters via query params (`name`, and `type`/`profile_id` for Event).
- Responses are plain JSON arrays; pagination metadata is read from response headers (confirm exact header names from the implementation / L220 spec).

## Goals

- No test asserts the `{items, has_more, next_cursor}` envelope or cursor params anymore.
- `test/e2e/test_resource.py` and `test/e2e/test_event.py` are rewritten to exercise header pagination, ordering, and filters end-to-end.
- Service tests for the migrated/paginated domains assert the new signatures and behaviors (delegation to `api_utils.services` where applicable; offset/size scoping for Encounter; Plan pagination).
- The stale `items` reference in `test/routes/test_profile_routes.py` is reconciled with the L200 dashboard decision.
- Full suites pass: `pipenv run test` and `pipenv run e2e`.

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
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `test/e2e/test_resource.py` — rewrite for header pagination + filters + ordering
- `test/e2e/test_event.py` — rewrite for header pagination + `type`/`profile_id` filters + `EVENT_LIST_ORDER`
- `test/services/test_resource_service.py` — assert delegation + retained CRUD
- `test/services/test_event_service.py` — assert delegation + retained by-id/create
- `test/services/test_path_service.py` — assert delegation + retained CRUD
- `test/services/test_plan_service.py` — assert pagination/ordering/name filter
- `test/services/test_encounter_service.py` — assert scoped pagination + default full-list
- `test/routes/test_profile_routes.py` — reconcile stale `items` expectation with L200 dashboard decision

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
