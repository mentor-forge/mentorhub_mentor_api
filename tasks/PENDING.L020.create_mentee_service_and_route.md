# L020 – Create the Mentee service and route

**Status**: Pending  
**Type**: Feature  
**Depends On**: L010  
**Description**: Implement the Mentee domain described by the L010 contract: a `MenteeService` that owns the mentee-notes document (read with create-if-missing, plus update) and a `/api/mentee` blueprint exposing `GET /api/mentee/{profile_id}` and `PATCH /api/mentee/{mentee_id}`. Follow the existing service/route patterns in this repo.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml` (the `Mentee` / `MenteeUpdate` contract from L010)

Pattern references (mirror these):

- `src/services/encounter_service.py` — service + `MongoIO` usage, RBAC, breadcrumb/token handling
- `src/routes/encounter_routes.py` — blueprint factory (`create_*_routes`), `create_flask_token`, `create_flask_breadcrumb`, `@handle_route_exceptions`
- `src/server.py` — blueprint registration with `url_prefix`
- `../mentorhub_mongodb_api/configurator/dictionaries/Mentee.*.yaml` — backing collection/schema (note id types are BSON `ObjectId`)

## Goals

- `src/services/mentee_service.py` with a `MenteeService`:
  - `get_mentee(profile_id, token, breadcrumb)` — return the mentee-notes document for `profile_id`; **create a default document if none exists** so callers always receive a valid document.
  - `update_mentee(mentee_id, data, token, breadcrumb)` — update the document; reject system-managed fields (`_id`, `created`, `saved`); set `saved` from the breadcrumb; `404` when the document is missing.
  - Convert string ids to `ObjectId` before querying/persisting (matches the collection schema).
  - RBAC: follow the **existing** permission pattern used by sibling services (e.g. mentor access). Adopting shared `Config` role constants and adding `admin` is handled later in L050 — do not introduce the constants here.
- `src/routes/mentee_routes.py` with `create_mentee_routes()`:
  - `GET /<profile_id>` → `MenteeService.get_mentee`
  - `PATCH /<mentee_id>` → `MenteeService.update_mentee`
- `src/server.py` registers the blueprint at `url_prefix='/api/mentee'`.
- Behavior matches the L010 OpenAPI contract.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - New `test/services/test_mentee_service.py`: get (existing + create-if-missing), update success, restricted-field rejection, not-found, RBAC allow/deny.
  - New `test/routes/test_mentee_routes.py`: `GET`/`PATCH` success, forbidden, unauthorized.
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - New `test/e2e/test_mentee.py`: `GET` auto-create + idempotency, then `PATCH` round-trip, plus auth required.
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API.

## Outputs

Paths are relative to the **API repository root**.

- `src/services/mentee_service.py` — new `MenteeService`
- `src/routes/mentee_routes.py` — new `create_mentee_routes()` blueprint
- `src/server.py` — import and register the mentee blueprint at `/api/mentee`
- `test/services/test_mentee_service.py` — new unit tests
- `test/routes/test_mentee_routes.py` — new unit tests
- `test/e2e/test_mentee.py` — new e2e tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
