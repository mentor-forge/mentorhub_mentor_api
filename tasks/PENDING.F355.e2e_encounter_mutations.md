# F355 – E2E Integration and Boundary Tests for Encounter Mutations

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F354_start_and_finish_encounter_mutations`  
**Description:** Implement comprehensive end-to-end (E2E) integration and adversarial boundary tests for all Encounter mutations in `test/e2e/test_encounter.py`. Test the full lifecycle: `POST /api/encounter/schedule` -> `POST /api/encounter/<id>/start` -> `PATCH /api/encounter/<id>` -> `POST /api/encounter/<id>/finish`. Verify customer subscription balance decrement, event creation, restricted PATCH behavior on active vs non-active statuses, and `mentor_name` / `mentee_name` lookup enrichment across all responses.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Bearer JWT validation, least-privilege testing, adversarial boundary cases
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md` — Mandatory Pre-PR QA Gate: `pipenv run container && pipenv run api && pipenv run e2e`
- `README.md`
- `docs/openapi.yaml`
- `test/e2e/test_encounter.py` — existing encounter E2E test suite
- `test/e2e/e2e_auth.py` — token minting helpers and personas

## Goals

- In `test/e2e/test_encounter.py`:
  - **Schedule Encounters E2E**:
    - Test `POST /api/encounter/schedule` with valid mentor, mentee, start date, day of week, time of day, count=2, and plan_id.
    - Verify response code `201`.
    - Verify array of 2 encounter documents is returned, each having `status: "scheduled"`, valid `appointment.from` / `appointment.to`, and auto-filled `agenda`.
    - Verify `mentor_name` and `mentee_name` are populated on each returned encounter.
  - **Start Encounter E2E**:
    - Test `POST /api/encounter/<id>/start` on a scheduled encounter.
    - Verify response code `200` and updated status `"active"`.
    - Verify corresponding event is recorded in the Event collection.
    - Negative test: attempt to start encounter when mentee's customer has zero subscription balance (expect `403`).
    - Negative test: attempt to start encounter that is already `"active"` or `"complete"` (expect `403` or `400`).
  - **PATCH Encounter E2E Guardrails**:
    - Test `PATCH /api/encounter/<id>` on the active encounter updating allowed fields (`agenda`, `transcript`, `summary`, `tldr`). Verify `200` and updated values.
    - Negative test: attempt to PATCH an encounter while in `"scheduled"` status (expect `403`).
    - Negative test: attempt to PATCH an encounter while in `"complete"` status (expect `403`).
    - Negative test: attempt to PATCH disallowed fields (e.g. `status`, `mentor_id`, `plan_id`) on an active encounter (expect `403`).
  - **Finish Encounter E2E**:
    - Test `POST /api/encounter/<id>/finish` on the active encounter.
    - Verify response code `200` and updated status `"complete"`.
    - Negative test: attempt to finish an encounter that is not in `"active"` status (expect `403` or `400`).
  - **Name Enrichment E2E**:
    - Verify `GET /api/encounter?mentee_id=...` and `GET /api/encounter/<id>` return documents containing `mentor_name` and `mentee_name`.
  - **Adversarial & RBAC Boundaries**:
    - Test that a non-owning mentor cannot start, patch, or finish an encounter (expect `403`).
    - Test unauthenticated requests return `401`.

### Craftsmanship Expectations

- Tests must verify architectural boundaries and failure modes, not only happy-path success.
- Test adversarial cases: least-privileged personas, non-owning mentors, invalid status transitions, and unauthorized field mutations.
- Keep helper functions clean and self-contained within `test/e2e/`.

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

- `test/e2e/test_encounter.py`

The agent must not update files outside this list.

## Execution Notes
