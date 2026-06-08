# L100

**Status**: Planned  
**Task Type**: Update
**Run Mode**: Run as needed  <!-- options: Sequential | Run as needed -->

## Goal

Update OpenAPI Specifications based on updated MongoDB Schemas. Add or update data schema's for all endpoints that accept or return data. 

## Context / Input files

These files must be treated as **inputs** and read before implementation:

- `{{info.slug}}_{{service.name}}_api/README.md`
- `{{info.slug}}_{{service.name}}_api/docs/openapi.yaml`

After using ``make schemas`` from /{{info.slug}}/Makefile to generate schema's for input, the agent may also consult:

- `{{info.slug}}/DeveloperEdition/standards/api_standards.md`
- `{{info.slug}}/Specifications/schemas/`

## Requirements

- Update existing routes and data schema to match the generated schema's. 

## Testing expectations

- **Unit tests**
  - Ensure that openapi.yaml passes validation

- **End‑to‑end (e2e) tests**
  - Use curl /docs/openapi.yaml to verify the correct file is served from the container

## Packaging / build checks

Before marking this task as completed:

- Ensure the project builds successfully:
  - Example: `pipenv run build`, `pipenv run container`, or project‑specific equivalent.
- Run the standard test commands:
  - Example: `pipenv run test`, `pipenv run e2e`, or project‑specific equivalent.
- Confirm that there are no new linter or type‑checking errors.

## Dependencies / Ordering

## Change control checklist

- [ ] Reviewed all **Context / Input files**.
- [ ] Designed and documented the solution approach in this file.
- [ ] Implemented code changes.
- [ ] Ran unit tests; all passing.
- [ ] Ran packaging/build steps; build successful.
- [ ] Ran e2e tests against packaged runtime
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

