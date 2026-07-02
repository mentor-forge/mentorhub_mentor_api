# L130 – Get Path by id: OpenAPI-only alignment

**Status**: Pending  
**Type**: Feature  
**Depends On**: L120  
**Description**: Align the `GET /api/paths/{PathId}` operation in `docs/openapi.yaml` with the finalized Path read contract. This is an **OpenAPI-only change** — no route, service, or test code changes. The endpoint remains readable by any authenticated caller (no role restriction on single-document reads), so the operation must document the read contract accurately and consistently with the other Path operations. Chained after L120 solely to serialize edits to `docs/openapi.yaml` and avoid merge conflicts.

## Context

Always read these files before starting work:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml` (after L120)

Additional inputs:

- `docs/openapi.yaml` — the `GET /api/paths/{PathId}` operation (`operationId: getPath`): summary, description, `PathId` path parameter, and the `200` / `401` / `404` / `500` responses. Reference the `#/components/schemas/Path` schema and the shared `#/components/responses/*` entries used elsewhere in the file.
- `src/routes/path_routes.py` and `src/services/path_service.py` — **read-only reference** to confirm actual behavior (auth-only, returns the full Path document, `404` when missing). Do not edit these files in this task.

## Goals

- `GET /api/paths/{PathId}` documentation accurately reflects behavior: returns the full `#/components/schemas/Path` document for any authenticated caller; no role/RBAC requirement is implied (no `403` response is added for reads).
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

- `docs/openapi.yaml` — `getPath` (`GET /api/paths/{PathId}`) operation description/response alignment only.

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._