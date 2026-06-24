# L070 – Implement Plan `steps` ⇄ `checklist` mapping in service + tests

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L060  
**Description**: Implement the API↔storage mapping for the Plan list field. The API contract uses `steps`; MongoDB stores `checklist` (per the `Plan` data dictionary, `additional_properties: false`). `PlanService` translates `steps`→`checklist` on the way into Mongo (create/update) and `checklist`→`steps` on the way out (get one, list items), and validates `steps` input. Routes need no change (they pass the request body and return the service result).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml` (after L060)

Additional inputs:

- `src/services/plan_service.py` — current generic pass-through service.
- `src/routes/plan_routes.py` — no change expected; confirm it forwards the JSON body and jsonifies the service result.
- `../mentorhub_mongodb_api/configurator/dictionaries/Plan.0.1.0.yaml` — storage field is `checklist`.
- `test/services/test_plan_service.py`, `test/routes/test_plan_routes.py`, `test/e2e/test_plan.py`.

## Goals

- Add a single source of truth for the mapping (e.g. `_STORAGE_LIST_FIELD = "checklist"`, `_API_LIST_FIELD = "steps"`).
- `create_plan`: if `steps` present in input, validate it then store it under `checklist`; never persist a top-level `steps` key (would fail Mongo validation).
- `update_plan`: same `steps`→`checklist` mapping for `$set`; keep rejecting restricted fields (`_id`, `created`, `saved`); validate `steps` when present.
- `get_plan` and `get_plans`: map stored `checklist`→`steps` in the returned document(s) so the API only ever exposes `steps`.
- Input validation for `steps` (raise `HTTPBadRequest`): must be a list; each item a non-empty string ≤255 chars with no tab/newline (matching the spec pattern); enforce a sensible max count (e.g. 100).
- No direct cross-collection access; keep service-to-service / standards conventions.

## Testing Expectations

- `pipenv run test` — unit tests (pytest). Add/extend:
  - create with `steps` persists `checklist` (and no `steps`) in the create payload.
  - update with `steps` sets `checklist` in `set_data`.
  - `get_plan`/`get_plans` return `steps` (mapped from a stored `checklist`) and not `checklist`.
  - validation: non-list `steps`, non-string/empty item, and over-max count each raise `HTTPBadRequest`.
- `pipenv run build` — compile sources.
- `pipenv run lint` — `black --check`.
- **E2E deferred**: `test/e2e/test_plan.py` may add a `steps` round-trip, but real writes require the configurator/db (`pipenv run db && pipenv run dev && pipenv run e2e`); run when infra is available.

## Outputs

Paths are relative to the **API repository root**.

- `src/services/plan_service.py` — add mapping + validation.
- `test/services/test_plan_service.py` — add `steps` mapping/validation tests.
- `test/e2e/test_plan.py` — (optional) add a `steps` round-trip e2e (kept `@pytest.mark.e2e`).

The agent must not update files outside this list.

## Execution Notes

**Summary of changes**:
- `src/services/plan_service.py`:
  - Added constants `API_LIST_FIELD = "steps"`, `STORAGE_LIST_FIELD = "checklist"`, `MAX_STEPS = 100`, `MAX_STEP_LENGTH = 255`.
  - `_validate_steps`: list of non-empty single-line strings, ≤255 chars each, ≤100 items, else `HTTPBadRequest`.
  - `_map_steps_to_storage`: shallow-copies inbound data, validates+renames `steps`→`checklist`; never leaves a top-level `steps` (which Mongo would reject).
  - `_map_checklist_to_api`: renames stored `checklist`→`steps` on the way out (no-op when absent / falsy — never invents an empty `steps`).
  - Wired mapping into `create_plan` (in), `update_plan` (in + out), `get_plan` (out), `get_plans` (each item out). Added `HTTPBadRequest` to the re-raise tuples in `create_plan`/`update_plan` so validation surfaces as 400 (not wrapped to 500).
- Routes unchanged — they forward the JSON body and jsonify the service result, so the mapping is transparent to the route layer.
- `test/services/test_plan_service.py`: added `steps`→`checklist` create/update, `checklist`→`steps` get/list, and validation tests (non-list, non-string, empty, tab/newline, over-length, over-count).

**Testing results**
- `pipenv run test`: 195 passed, 29 deselected (e2e).
- Plan-only: `test_plan_service.py` + `test_plan_routes.py` = 30 passed.
- `pipenv run build`: OK.
- `pipenv run lint`: edited files formatted with `black`; pre-existing `black` findings in unrelated files left untouched.

**Follow-ups**
- E2E `steps` round-trip not added/run yet — requires live configurator+db (`pipenv run db && pipenv run dev && pipenv run e2e`). Existing `test/e2e/test_plan.py` left unchanged.
- When the Encounter feature lands ("populate the checklist from the plan"), it reads the stored `checklist` directly — consistent with this storage field.
