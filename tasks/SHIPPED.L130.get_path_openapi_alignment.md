# L130 – Get Path by id: OpenAPI-only alignment

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L120  
**Description**: Align the `GET /api/path/{PathId}` operation in `docs/openapi.yaml` with the finalized Path read contract. This is an **OpenAPI-only change** — no route, service, or test code changes. The endpoint remains readable by any authenticated caller (no role restriction on single-document reads), so the operation must document the read contract accurately and consistently with the other Path operations. Chained after L120 solely to serialize edits to `docs/openapi.yaml` and avoid merge conflicts.

## Context

Always read these files before starting work:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml` (after L120)
- `../mentorhub_api_utils/README.md`

**Prerequisites (local infra & schema source of truth)**

Before starting work, start the backing database and verify the schema source of truth:

- Start the backing database locally: `pipenv run db`
- Verify the schema source of truth (trailing slash required):
  `curl http://localhost:8383/api/configurations/json_schema/Path.yaml/latest/`

Additional inputs:

- `docs/openapi.yaml` — the `GET /api/path/{PathId}` operation (`operationId: getPath`): summary, description, `PathId` path parameter, and the `200` / `401` / `404` / `500` responses. Reference the `#/components/schemas/Path` schema and the shared `#/components/responses/*` entries used elsewhere in the file.
- `src/routes/path_routes.py` and `src/services/path_service.py` — **read-only reference** to confirm actual behavior (auth-only, returns the full Path document, `404` when missing). Do not edit these files in this task.

## Goals

- `GET /api/path/{PathId}` documentation accurately reflects behavior: returns the full `#/components/schemas/Path` document for any authenticated caller; no role/RBAC requirement is implied (no `403` response is added for reads).
- Summary/description wording is clear and consistent with the other Path operations (e.g. phrasing and shared response refs); the `200` response references `#/components/schemas/Path`, and `401` / `404` / `500` use the shared `#/components/responses/*` entries.
- The `PathId` path parameter (`pattern`, `example`, `required: true`) is correct and consistent with other id path parameters in the spec.
- No changes to route handlers, services, or tests — this task edits `docs/openapi.yaml` only.

## Testing Expectations

Run all commands from the API repository root.

- **Spec validity** — confirm `docs/openapi.yaml` remains valid YAML and the API explorer renders (no broken `$ref`s). If the repo exposes a spec-lint or explorer smoke test, run it.
- **Unit tests** — `pipenv run test` should remain green (no code changed).
- **Lint / build** — `pipenv run lint`, `pipenv run build`.
- **Packaging verification** — `pipenv run container`, `pipenv run api`, then `curl -s http://localhost:8391/docs/openapi.yaml | head` to confirm the updated spec is served.

## Outputs

Paths are relative to the API repository root.

- `docs/openapi.yaml` — `getPath` (`GET /api/path/{PathId}`) operation description/response alignment only.

The agent must not update files outside this list.

## Execution Notes

### Changes

- `docs/openapi.yaml` — `getPath` (`GET /api/path/{PathId}`) only. Description now reads "Retrieve a specific Path document by its PathId. Readable by any authenticated caller (no role restriction)." and the `200` description was clarified to "Successfully retrieved the Path document". Responses remain `200`/`401`/`404`/`500` with **no `403`** (reads are not role-restricted); `200` still references `#/components/schemas/Path` and the `PathId` path parameter is unchanged.
- No route/service/test code changed (OpenAPI-only task).

### Test results

- OpenAPI parses as valid YAML; `getPath` responses = `['200','401','404','500']` (verified via `yaml.safe_load`).
- `pipenv run test` → **191 passed, 30 deselected** (unchanged; no code touched).
- Packaging/explorer check (`pipenv run api` + curl `/docs/openapi.yaml`) deferred — container infra not available in this environment.