# L110 – Remove the Encounter list endpoint (GET /api/encounter)

**Status**: Shipped  
**Type**: Refactor  
**Depends On**: L080  
**Description**: Remove the unused `GET /api/encounter` infinite-scroll list endpoint. Nothing consumes it — the app lists a mentee's encounters via Get Profile (the Profile composite uses `EncounterService.get_encounters_for_mentee`). Delete the list route and its backing `EncounterService.get_encounters` (the generic infinite-scroll list), keeping POST `/api/encounter`, GET-by-id, PATCH, and the per-mentee helpers (`get_encounters_for_mentee`, `get_recent_encounter`) intact.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml` (after L080 removes the list operation from the contract)

Additional inputs:

- `src/routes/encounter_routes.py` — `get_encounters` route bound to `GET ''` on the blueprint; remove it (and update the module docstring that enumerates endpoints).
- `src/services/encounter_service.py` — remove the generic `get_encounters` list method and the now-unused `ALLOWED_SORT_FIELDS` / `execute_infinite_scroll_query` import **only if** they are not referenced elsewhere. Do **not** remove `get_encounters_for_mentee` or `get_recent_encounter` (still used by the Profile composite).
- `test/routes/test_encounter_routes.py`, `test/services/test_encounter_service.py`, `test/e2e/test_encounter.py` — remove tests that target the deleted list endpoint/method.
- `src/server.py` — confirm route registration still works (the blueprint is registered as a whole; no change expected, but verify).

## Goals

- The `GET /api/encounter` list route is removed from `encounter_routes.py`; the POST on the same path remains.
- `EncounterService.get_encounters` (generic list) is removed; `get_encounters_for_mentee` and `get_recent_encounter` remain and continue to back the Profile composite.
- Unused imports/constants left by the removal (`execute_infinite_scroll_query`, `ALLOWED_SORT_FIELDS`) are deleted only if no longer referenced.
- All tests referencing the removed list endpoint/method are deleted or updated; the remaining suite passes.
- No other endpoint or the Profile composite regresses (Get Profile still returns the mentee's encounters).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests** — `pipenv run test`. Remove list-endpoint tests; confirm Profile composite / per-mentee encounter tests still pass.
- **Lint / build** — `pipenv run lint`, `pipenv run build` (no unused-import/lint regressions).
- **Dev / E2E (when infra available)** — `pipenv run db`, `pipenv run dev`, `pipenv run e2e`; remove/adjust `test/e2e/test_encounter.py` list cases and confirm `GET /api/encounter` now returns `404`/`405` while Get Profile still lists encounters.

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/encounter_routes.py` — remove the list route and update the endpoint docstring.
- `src/services/encounter_service.py` — remove the generic `get_encounters` list method and any now-unused imports/constants.
- `test/routes/test_encounter_routes.py` — remove list-route tests.
- `test/services/test_encounter_service.py` — remove `get_encounters` list tests.
- `test/e2e/test_encounter.py` — remove/adjust list-endpoint e2e cases.
- `test/test_server.py` — update stale `test_encounter_routes_registered` assertion after list-endpoint removal.

The agent must not update files outside this list.

## Execution Notes

### Changes

- `src/routes/encounter_routes.py` — Removed the `GET ''` list route (`get_encounters` view) and dropped its line from the module docstring. Kept `POST ''` (`create_encounter`), `GET /<encounter_id>`, and `PATCH /<encounter_id>`. File reformatted with black.
- `src/services/encounter_service.py` — Removed the generic `EncounterService.get_encounters` infinite-scroll method plus the now-unused `from api_utils.mongo_utils import execute_infinite_scroll_query` import and the `ALLOWED_SORT_FIELDS` constant. Kept `get_encounters_for_mentee` and `get_recent_encounter` (Profile composite), plus `create_encounter`, `get_encounter`, `update_encounter`, and helpers. `DESCENDING`/`ObjectId`/`InvalidId`/exception imports remain in use.
- `test/routes/test_encounter_routes.py` — Removed 2 list-route tests (`test_get_encounters_no_filter`, `test_get_encounters_with_name_filter`).
- `test/services/test_encounter_service.py` — Removed 7 list-method tests (`test_get_encounters_first_batch`, four validation tests, `test_get_encounters_invalid_after_id`, `test_get_encounters_handles_exception`). Kept per-mentee / Profile-composite / RBAC tests.
- `test/e2e/test_encounter.py` — Removed the two list e2e tests; added `test_get_encounter_list_endpoint_removed` (expects 404/405) and repointed `test_encounter_endpoints_require_auth` at `GET /api/encounter/<id>` (still 401).
- `test/test_server.py` — Updated the stale `test_encounter_routes_registered` assertion: `GET /api/encounter` now returns 405 (only POST bound), so the test confirms registration via `GET /api/encounter/<id>` instead. File reformatted with black.

`src/server.py` registration was verified correct and left unchanged (blueprint registered whole).

### Test results

- `pipenv run test`: **195 passed, 0 failed, 30 deselected** (e2e markers).
- `pipenv run build`: passes.
- `pipenv run lint`: edited files (`encounter_routes.py`, `encounter_service.py`, `test_encounter_routes.py`, `test_encounter_service.py`, `test/e2e/test_encounter.py`, `test/test_server.py`) are black-clean; pre-existing unrelated lint failures untouched.
- E2E (`pipenv run e2e`) deferred — requires running API + Mongo infra; covered by deselected markers.
