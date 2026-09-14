# F361 – Update Encounter E2E tests for new test data and mutation actual datetimes

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F360_encounter_start_finish_actual_datetimes`  
**Description:** Update E2E integration tests in `test/e2e/test_encounter.py` to verify start/finish mutation `actual` timestamps and validate the expanded Encounter seed test data (including `actual` appointment windows, `no_show` flags, and Obsidian transcripts/summaries). Run full test suite and mandatory Pre-PR QA Gate.

## Path Anchoring

All paths are relative to **this API repository root** (the directory that contains `Pipfile`).

- Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
- In-repo: `test/e2e/test_encounter.py`, `tasks/`

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `tasks/PENDING.F359.encounter_openapi_schema.md`
- `tasks/PENDING.F360.encounter_start_finish_actual_datetimes.md`
- `docs/openapi.yaml`
- `src/services/encounter_service.py`
- `test/e2e/test_encounter.py`
- Running schema server endpoint: `http://localhost:8383/api/configurations/json_schema/Encounter.yaml/latest/`

## Goals

- In `test/e2e/test_encounter.py`:
  - **Update `test_encounter_full_lifecycle_start_patch_finish_e2e`**:
    - Verify that `POST /api/encounter/<id>/start` response includes `actual` dictionary with a valid `"from"` date-time string.
    - Verify that `POST /api/encounter/<id>/finish` response includes `actual` dictionary with both `"from"` and `"to"` date-time strings.
    - Verify that a subsequent `GET /api/encounter/<id>` returns the persisted `actual` with both `"from"` and `"to"`.
  - **Add seeded encounter verification tests**:
    - `test_seeded_encounter_completed_with_actual_and_transcripts_e2e`:
      - Query seeded completed encounter (e.g. `e00000000000000000000001`) via `GET /api/encounter/e00000000000000000000001`.
      - Assert status is `"complete"`.
      - Assert `actual` contains `"from"` and `"to"` date-time strings.
      - Assert `appointment` contains `"from"` and `"to"` date-time strings.
      - Assert `no_show` is `False`.
      - Assert `summary`, `tldr`, and `transcript` are present and non-empty strings.
      - Assert `mentor_name` and `mentee_name` are populated via profile enrichment.
    - `test_seeded_encounter_no_show_e2e`:
      - Query seeded no-show encounter (e.g. `e00000000000000000000007`) via `GET /api/encounter/e00000000000000000000007`.
      - Assert status is `"complete"`.
      - Assert `no_show` is `True`.
      - Assert `mentor_name` and `mentee_name` are populated via profile enrichment.
    - `test_seeded_encounter_scheduled_appointment_e2e`:
      - Query seeded scheduled encounter (e.g. `e00000000000000000000009`) via `GET /api/encounter/e00000000000000000000009`.
      - Assert status is `"scheduled"`.
      - Assert `appointment` contains scheduled `"from"` and `"to"` windows.
      - Assert `actual` is not present (or empty).
      - Assert `no_show` is `None` or `False`.
  - **Adversarial boundary check**:
    - In `test_patch_encounter_disallowed_fields_rejected_e2e`, ensure `actual` and `no_show` cannot be directly injected or overwritten via `PATCH` when active.

### Craftsmanship Expectations

- Tests must be idempotent, repeatable, and non-destructive to seeded database state.
- Validate real schema responses against live running API endpoints.
- Ensure 100% test pass rate across unit, route, and E2E suites.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests & Linting**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **E2E Suite**:
  - `pipenv run pytest test/e2e/test_encounter.py`
- **Mandatory Pre-PR QA Gate (E2E & Packaging)**:
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e` — 100% of E2E tests must pass against the running containerized stack.

## Outputs

- `test/e2e/test_encounter.py`

The agent must not update files outside this list.

## Execution Notes

<!-- Reserved for task execution agent to record plan, commands run, test results, and follow-ups. -->
