# L220 – OpenAPI sweep: remove infinite-scroll schemas, document header pagination

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L210_harvest_alignment_read_paths  
**Description**: Sweep `docs/openapi.yaml` to remove the cursor/infinite-scroll response schemas and document **header-based pagination** on every `GET` list operation. Each list endpoint should describe the `offset`/`size` request headers, the pagination response headers, and the standardized `sort_by`/`order` (and any filter) query params, consistent with the migrations in L160–L200.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `docs/openapi.yaml`
- `src/routes/` (all route modules, to mirror the actual request/response contract)

**Current state**

- `docs/openapi.yaml` still defines `components.schemas.InfiniteScrollResponse` (required `items`, `limit`, `has_more`, `next_cursor`) at ~lines 2188–2214. Search the whole file for any `$ref` to it and for residual `after_id`/`limit`/`next_cursor`/`has_more` wording on list operations.
- List operations to cover: `GET /api/resource`, `GET /api/event`, `GET /api/path`, `GET /api/plan`, the mentee-scoped Encounter read, and `GET /api/profile` (dashboard — reflect the L200 pagination/no-pagination decision).

**Pagination header contract (api_utils 0.5.0)**

- Document the exact request/response pagination headers and `order_spec`-driven `sort_by`/`order` params implemented in L160–L200. Confirm header names against the implementation and record them in **Execution Notes** so the spec matches runtime behavior.

## Goals

- `InfiniteScrollResponse` schema and all `$ref`s to it are removed from `docs/openapi.yaml`.
- No residual cursor-pagination params (`after_id`, `limit`, `next_cursor`, `has_more`) remain on any list operation.
- Every `GET` list operation documents:
  - `offset`/`size` request headers (as header parameters) for pagination.
  - The pagination response headers emitted by the API.
  - Standardized `sort_by`/`order` query params and any supported filter params.
  - A plain array response body (the domain item schema), not an envelope.
- The dashboard (`GET /api/profile`) reflects the L200 decision (paginated headers, or documented full read).
- `docs/openapi.yaml` remains valid and is served by the packaged API.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Spec validation**
  - `pipenv run lint`
  - `pipenv run build`
  - Confirm `InfiniteScrollResponse` is gone: no matches when searching `docs/openapi.yaml` for `InfiniteScrollResponse`, `after_id`, `next_cursor`, `has_more`.
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev`
  - `pipenv run e2e`
  - Verify served spec: `curl -s http://localhost:8391/docs/openapi.yaml | head`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — remove `InfiniteScrollResponse` and its `$ref`s; document header pagination + `sort_by`/`order` + filters on every `GET` list operation; align dashboard operation with the L200 decision

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
