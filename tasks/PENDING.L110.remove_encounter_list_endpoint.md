# L110 – Remove the Encounter list endpoint (GET /api/encounter)

**Status**: Pending  
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

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
