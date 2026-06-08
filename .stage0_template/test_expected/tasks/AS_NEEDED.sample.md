# T900 – Example: Add healthcheck endpoint to runbook API

**Status**: Planned  
**Task Type**: Feature  
**Run Mode**: Run as needed  <!-- options: Sequential | Run as needed -->

## Goal

Add a `/health` HTTP endpoint to the runbook API that:
- Returns `200 OK` when the service and its dependencies are healthy.
- Exposes basic version/build information.

## Context / Input files

These files must be treated as **inputs** and read before implementation:

- `{{info.slug}_{{service.name}}_api/README.md`
- `{{info.slug}_{{service.name}}_api/docs/openapi.yaml`

The agent may also consult:

- Existing healthcheck implementations in sibling services (if any).
- `{{info.slug}}/Contributing.md`
- `{{info.slug}}/DeveloperEdition/standards/api_standards.md`

## Requirements

- Implement a `/health` endpoint that:
  - Returns a JSON body with at least: `status`, `service`, `version`.
  - Performs a lightweight check of any critical backing services (e.g., database connectivity) if feasible.
- Update OpenAPI documentation to describe the new endpoint.
- Ensure the endpoint is covered by:
  - Unit tests (route handler, helper functions).
  - e2e tests (end‑to‑end request/response path).

## Testing expectations

- **Unit tests**
  - Add or update tests under `tests/unit/` that cover:
    - Happy‑path response (status 200, correct JSON shape).
    - Failure handling if a dependency is down (if applicable).

- **End‑to‑end (e2e) tests**
  - Add or update e2e tests under `tests/e2e/` that:
    - Start the service (or use existing fixture).
    - Call `/health` and assert a successful response.

## Packaging / build checks

Before marking this task as completed:

- Ensure the project builds successfully:
  - Example: `pipenv run build`, `pipenv run container`, or project‑specific equivalent.
- Run the standard test commands:
  - Example: `pipenv run test`, `pipenv run e2e`, or project‑specific equivalent.
- Confirm that there are no new linter or type‑checking errors.

## Dependencies / Ordering

- Should run **after**:
  - `R000.PENDING.project_bootstrap.md` (if present).
- Should run **before**:
  - `R010.PENDING.add_production_alerting.md` (if present).

## Change control checklist

- [ ] Reviewed all **Context / Input files**.
- [ ] Designed and documented the solution approach in this file.
- [ ] Implemented code changes.
- [ ] Added/updated **unit tests**.
- [ ] Added/updated **e2e tests**.
- [ ] Ran unit tests and e2e tests; all passing.
- [ ] Ran packaging/build steps; build successful.
- [ ] Performed any necessary manual verification (if applicable).
- [ ] Created a scoped commit referencing this task ID.

## Implementation notes (to be updated by the agent)

**Summary of changes**
- _e.g., "Added `/health` route in `app/routes/health.py`, updated `openapi.yaml`, created unit and e2e tests."_

**Testing results**
- Unit tests: _command(s) run, high‑level outcome_
- E2E tests: _command(s) run, high‑level outcome_
- Packaging/build: _command(s) run, high‑level outcome_

**Follow‑up tasks**
- _e.g., "Create a shared healthcheck utility in `py_utils` for reuse across services."_

