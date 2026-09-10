# F358 – Update Mentee route tests and E2E integration tests for simplified schema

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F357_mentee_service_schema_alignment`  
**Description:** Update Mentee route unit tests in `test/routes/test_mentee_routes.py` and E2E integration tests in `test/e2e/test_mentee.py` to use `summary` and `notes` instead of `focus`. Verify that `GET /api/mentee/<id>` auto-creates valid documents under the new schema, `PATCH` round-trips `summary` and `notes`, and all Pre-PR QA Gate tests pass.

## Path Anchoring

All paths are relative to **this API repository root** (the directory that contains `Pipfile`).

- Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
- In-repo: `test/routes/test_mentee_routes.py`, `test/e2e/test_mentee.py`, `tasks/`

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `tasks/SHIPPED.F356.mentee_openapi_schema.md`
- `tasks/SHIPPED.F357.mentee_service_schema_alignment.md`
- `docs/openapi.yaml`
- `src/services/mentee_service.py`
- `test/routes/test_mentee_routes.py`
- `test/e2e/test_mentee.py`
- Running schema server endpoint: `http://localhost:8383/api/dictionaries/Mentee.0.1.0.yaml/`

## Goals

- In `test/routes/test_mentee_routes.py`:
  - Update `test_update_mentee_success`:
    - Send update payload with `{"summary": "Mentoring summary", "notes": "Mentoring notes"}` instead of `{"focus": "async patterns"}`.
    - Verify mock is invoked with the updated payload and response returns the updated fields.
- In `test/e2e/test_mentee.py`:
  - Update `test_get_mentee_auto_create_and_idempotent`:
    - Verify auto-created document contains `summary: ""` and `notes: ""`.
    - Verify auto-created document does NOT contain `focus`, `homework`, `description`, `schedule`, or `next_appointment`.
  - Update `test_patch_mentee_round_trip`:
    - Send payload updating `summary` and `notes`:
      ```python
      payload = {"summary": "E2E relationship summary", "notes": "E2E mentor notes"}
      ```
    - Assert `patched_doc["summary"] == "E2E relationship summary"` and `patched_doc["notes"] == "E2E mentor notes"`.
    - Re-read via GET `/api/mentee/{PROFILE_ID}` and assert `summary` and `notes` persisted correctly.
  - Update `test_mentee_endpoints_require_auth`:
    - Change unauthenticated PATCH test payload from `{"focus": "nope"}` to `{"summary": "nope"}`.
  - Add adversarial boundary test:
    - Verify attempting to PATCH a legacy/dropped field (e.g. `{"focus": "invalid"}` or `{"homework": "invalid"}`) is rejected with `403 Forbidden`.

### Craftsmanship Expectations

- Maintain complete idempotency and repeatability in E2E tests.
- Ensure 100% test pass rate across unit, route, and E2E suites.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests & Linting**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Mandatory Pre-PR QA Gate (E2E & Packaging)**:
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e` — 100% of E2E tests must pass against the running containerized stack.

## Outputs

- `test/routes/test_mentee_routes.py`
- `test/e2e/test_mentee.py`

The agent must not update files outside this list.

## Execution Notes

