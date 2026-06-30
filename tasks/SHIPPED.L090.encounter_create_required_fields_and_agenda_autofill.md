# L090 – Encounter POST: require mentor_id/mentee_id/plan_id and auto-fill agenda from Plan

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L080  
**Description**: Implement the new create behavior for `POST /api/encounter`. The request must include `mentor_id`, `mentee_id`, and `plan_id`; missing or malformed values raise `400`. On create, the service looks up the referenced Plan and auto-fills the encounter's `agenda` from the Plan's `checklist` (each checklist sentence becomes an agenda item `{ "step": <sentence>, "checked": false }`). The client-supplied `agenda` (if any) is ignored/overwritten by the Plan-derived agenda.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml` (after L080)

Additional inputs:

- `src/services/encounter_service.py` — `create_encounter` is the primary change site.
- `src/services/plan_service.py` — how Plans are read (`PlanService.get_plan`); the API exposes the list as `steps`, but the **stored** field is `checklist`. Reuse `PlanService` rather than reaching into the Plan collection directly (no cross-collection access from EncounterService).
- `src/routes/encounter_routes.py` — `create_encounter` route (should keep forwarding the JSON body; no signature change expected).
- `../mentorhub_mongodb_api/configurator/dictionaries/Encounter.0.1.0.yaml` — `agenda` item shape `{checked: boolean, step: sentence}`.
- `../mentorhub_mongodb_api/configurator/dictionaries/Plan.0.1.0.yaml` — `checklist` is the source list.
- `test/services/test_encounter_service.py`, `test/routes/test_encounter_routes.py`, `test/e2e/test_encounter.py`.

## Goals

- `create_encounter` validates that `mentor_id`, `mentee_id`, and `plan_id` are present and are valid 24-hex ObjectId strings; otherwise raise `HTTPBadRequest` (surfaced as `400`). Add `HTTPBadRequest` to the re-raise tuple so it is not wrapped to `500`.
- The referenced Plan is fetched via `PlanService.get_plan(plan_id, token, breadcrumb)`. If the Plan does not exist, raise `HTTPNotFound` (`404`) — do not silently create an encounter with an empty agenda for a missing Plan.
- The encounter's `agenda` is built from the Plan's checklist: each checklist entry maps to `{ "step": <entry>, "checked": False }`. Any `agenda` provided in the request body is replaced by this derived agenda. An empty/absent checklist yields an empty `agenda` list (`[]`).
- Existing system-managed behavior is preserved: strip incoming `_id`, set `created` and `saved` from the breadcrumb.
- No direct cross-collection access from `EncounterService` to the Plan collection; go through `PlanService`. Follow the service/route separation-of-concerns standards.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests** — `pipenv run test`. Add/extend `test/services/test_encounter_service.py`:
  - create succeeds and produces `agenda` derived from the Plan checklist (each item `{step, checked: False}`), overriding any client-supplied `agenda`.
  - missing `mentor_id` / `mentee_id` / `plan_id` each raise `HTTPBadRequest` (`400`).
  - malformed (non-ObjectId) id raises `HTTPBadRequest`.
  - unknown `plan_id` raises `HTTPNotFound` (`404`).
  - empty/absent Plan checklist yields `agenda == []`.
  - Route test (`test/routes/test_encounter_routes.py`): POST with the three ids returns `201`; missing required field returns `400`.
- **Lint / build** — `pipenv run lint`, `pipenv run build`.
- **Dev / E2E (when infra available)** — `pipenv run db`, `pipenv run dev`, `pipenv run e2e`; extend `test/e2e/test_encounter.py` with a create-from-Plan round trip asserting the derived `agenda` (kept `@pytest.mark.e2e`).

## Outputs

Paths are relative to the **API repository root**.

- `src/services/encounter_service.py` — required-field validation, Plan lookup via `PlanService`, agenda auto-fill in `create_encounter`.
- `test/services/test_encounter_service.py` — create validation + agenda-autofill tests.
- `test/routes/test_encounter_routes.py` — POST 201 / 400 assertions for the create contract.
- `test/e2e/test_encounter.py` — (optional) create-from-Plan agenda round trip (`@pytest.mark.e2e`).

The agent must not update files outside this list.

## Execution Notes

### Summary of changes

- `src/services/encounter_service.py`:
  - Imported `PlanService` (`from src.services.plan_service import PlanService`) so the Plan is read through its service — no direct cross-collection access from `EncounterService`.
  - `create_encounter` now validates that `mentor_id`, `mentee_id`, and `plan_id` are present and valid ObjectId strings (`ObjectId.is_valid`); a missing or malformed value raises `HTTPBadRequest` (400).
  - Fetches the referenced Plan via `PlanService.get_plan(plan_id, token, breadcrumb)`; an unknown Plan's `HTTPNotFound` (404) propagates.
  - Added `_build_agenda_from_plan(plan)` which maps the Plan list to `agenda` items `{"step": <entry>, "checked": False}`. It reads `steps` first and falls back to `checklist` (robust to whichever field `PlanService.get_plan` returns), so an empty/absent list yields `agenda == []`. Any client-supplied `agenda` is replaced.
  - Re-raise tuple widened to `(HTTPForbidden, HTTPBadRequest, HTTPNotFound)` so 400/404 surface correctly instead of being wrapped to 500. System-managed behavior preserved (strip `_id`, set `created`/`saved` from breadcrumb).
- `test/services/test_encounter_service.py`: existing create tests updated to send the three valid ids and mock `PlanService.get_plan`; added tests for agenda-derived-from-plan (overriding client agenda), empty checklist -> `agenda == []`, each missing required id -> 400, malformed id -> 400, and unknown plan_id -> 404.
- `test/routes/test_encounter_routes.py`: POST success now sends the three ids; added a missing-required-field -> 400 route test.
- `test/e2e/test_encounter.py` (`@pytest.mark.e2e`): replaced the create test with a create-from-Plan round trip asserting the derived `agenda`, plus a missing-required-field -> 400 case.

### Test results

- `pipenv run test` — **192 passed, 29 deselected** (e2e excluded).
- `pipenv run lint` (`black --check`) — the 4 edited files are black-clean (verified explicitly: `black --check` on them exits 0). The repo has pre-existing black failures in unrelated files; those were not touched.
- `pipenv run build` — passed (exit 0).

### Deferrals / follow-ups

- E2E (`pipenv run db && pipenv run dev && pipenv run e2e`) not run — requires live db/configurator infra. The new e2e tests are kept `@pytest.mark.e2e` and excluded from `pipenv run test`.
- Note: the current `PlanService.get_plan` returns the stored `checklist` unchanged (the L070 `checklist`->`steps` mapping is not present in the live `plan_service.py`). The agenda builder reads `steps` then falls back to `checklist`, so it works regardless of which field is exposed.
