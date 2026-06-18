# T998 – Example: Update OpenAPI from MongoDB schema

**Status**: Run as needed  
**Type**: Feature  
**Depends On**: none  
**Description**: Parameterized template for updating `docs/openapi.yaml` (and any projecting route/service code) after MongoDB dictionary schemas change. Edit the parameter values under **Context** before promoting this task to `Pending`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml`

**Parameters (edit before running)**

- **API repository** (working directory for all commands and Outputs paths): `../mentorhub_mentor_api`
- **Collection / dictionary name**: `Profile`
- **OpenAPI schema(s) to update**: `Profile`, `MentorDashboardProfile` (when dashboard cards expose the field)
- **Field(s) to add or change**: `full_name` (`string`, optional) — display name distinct from IdP `name`
- **Generated JSON schema input**: `../mentorhub/Specifications/schemas/Profile.schema.json`
- **External prerequisite**: MongoDB `Profile` dictionary includes `full_name` and database has been reconfigured with current test data. Verify with `../mentorhub_mongodb_api/Tasks/PENDING.T106.mentee_collection_and_profile_schema.md` or the shipped successor task. If the dictionary or `Profile.schema.json` is not current, set **Status** to `Blocked` and stop.

**Schema generation (human or separate workflow, before this task)**

From the `mentorhub` repo with MongoDB configurator running:

```bash
make schemas
```

This writes JSON schemas to `../mentorhub/Specifications/schemas/`. Confirm `Profile.schema.json` contains the new field before proceeding.

**Additional input files** (paths relative to API repository root unless noted):

- Generated schema file named above
- `src/routes/profile_routes.py` (or domain routes for affected endpoints)
- `src/services/profile_service.py` (update when endpoints project an explicit field list)
- `test/routes/test_profile_routes.py`
- `test/services/test_profile_service.py`
- `test/e2e/test_profile.py`

## Goals

- `docs/openapi.yaml` component schemas match the generated MongoDB JSON schema for the affected collection(s), including new or changed properties, types, descriptions, and optionality.
- Route handlers and services return the new field where the API contract requires it (full document reads may pass through from MongoDB; aggregated/dashboard responses may need explicit projection updates).
- Unit tests (`pipenv run test`) pass.
- E2E tests (`pipenv run e2e`) pass against a running API.
- Packaged API serves the updated OpenAPI document at `/docs/openapi.yaml`.

## Testing Expectations

Run all commands from the **API repository root** named in Context.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`

- **Build**
  - `pipenv run build`

- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`

- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against containerized API
  - Verify OpenAPI is served: `curl -s http://localhost:8391/docs/openapi.yaml | head` (adjust port to match this API)

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add `full_name` to `Profile` (and `MentorDashboardProfile` if dashboard cards should expose it)
- `src/services/profile_service.py` — include `full_name` in dashboard card projection when applicable
- `test/services/test_profile_service.py` — update mocks/assertions for projected dashboard shape
- `test/e2e/test_profile.py` — assert `full_name` appears in `GET /api/profile/{id}` responses when present in test data

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
