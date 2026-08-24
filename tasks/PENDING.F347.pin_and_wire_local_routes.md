# F347 – Pin api-utils 1.0.0 and wire shared GET factories

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F346_profile_service_subclass`  
**Description:** F-RA13 owns this pin. Bump `api-utils` from `0.5.1` to `1.0.0`, mount `create_*_get_routes(LocalService)` from `api_utils.routes.shared_get_routes`, and add control POST/PATCH on the returned blueprints. Routes keep `from src.services.<x> import <Y>` — never import shared service **classes**. Drop `X-Pagination-*` response headers on Resource/Path/Plan/Event lists. Lands in the **same PR** as F340–F346.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Resource, Path, Plan, Encounter; **creates** Event; **consumes** Profile
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — routes are HTTP-only (token, breadcrumb, exceptions, payload pass-through)
- `tasks/_PLANNING.md` — `pipenv run install` after Pipfile changes (CodeArtifact; run `mh` first)
- `README.md`
- `../mentorhub_api_utils/README.md` — `create_*_get_routes(service_cls)` then add POST/PATCH on the returned blueprint; list GET is a JSON array; `offset`/`size` headers only
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py`
- `Pipfile` / `Pipfile.lock` — currently `api-utils==0.5.1`
- `src/server.py` — keep existing `/api/*` prefixes; factories return blueprints registered the same way
- `docs/openapi.yaml` — F340 list contract plus unchanged dashboard / control operations
- Local services from F341–F346: `src/services/resource_service.py`, `path_service.py`, `plan_service.py`, `encounter_service.py`, `mentee_service.py`, `event_service.py`, `profile_service.py`, `journey_service.py`
- Current routes: `src/routes/resource_routes.py`, `path_routes.py`, `plan_routes.py`, `profile_routes.py`, `mentee_routes.py`, `encounter_routes.py`, `event_routes.py`
- Route tests under `test/routes/`; patch targets stay `src.routes.<module>.<Service>.*`
- `test/e2e/` — drop `X-Pagination-*` assertions; add encounter list GET coverage
- `test/e2e/e2e_auth.py` — tokens must include `profile_id` (already present)

**External prerequisite:** `api-utils==1.0.0` must resolve from the CodeArtifact index. If `pipenv run install` cannot resolve 1.0.0, set **Status** to `Blocked` and stop.

**Pin:** this task (F-RA13) owns `api-utils==1.0.0`. Install with `pipenv run install`. Do **not** use bare `pipenv install`. Use `scripts/pipenv-lock.sh` if lock hashes must be regenerated first.

**Why pin is last:** 1.0.0 strips Plan/Encounter/Mentee writes and Mentor Dashboard enrich from shared classes. Subclasses in F341–F346 restore those methods; this task switches GET handlers to factories and then pins so `pipenv run test` stays green.

### Route mapping

| File | After |
| --- | --- |
| `src/routes/resource_routes.py` | `bp = create_resource_get_routes(ResourceService)` then `POST ""` → `create_resource` (`201`) and `PATCH /<resource_id>` → `update_resource` |
| `src/routes/path_routes.py` | `bp = create_path_get_routes(PathService)` then POST create and PATCH update |
| `src/routes/plan_routes.py` | `bp = create_plan_get_routes(PlanService)` then POST create and PATCH update |
| `src/routes/profile_routes.py` | `bp = create_profile_get_routes(ProfileService)` — list/by-id use subclass dashboard / `ProfileDetail`. Then local `GET /<profile_id>/properties` → `get_profile_properties`. **No POST/PATCH.** |
| `src/routes/mentee_routes.py` | `bp = create_mentee_get_routes(MenteeService)` then `PATCH /<mentee_id>` → `update_mentee` |
| `src/routes/encounter_routes.py` | `bp = create_encounter_get_routes(EncounterService)` (list requires `mentee_id` + by-id) then POST create and PATCH update |
| `src/routes/event_routes.py` | `bp = create_event_get_routes(EventService)` then `POST ""` → `create_event` (`201`) and keep local `GET /<event_id>` → `get_event` (factory is list-only) |

Filter/order constants may still come from `api_utils` via factory MRO lookup. Keep re-exports on local service modules if routes still import them. Do **not** `from api_utils.services import ResourceService` (or any other `*Service`) in any route module.

POST/PATCH handlers: `create_flask_token()`, `create_flask_breadcrumb(token)`, `request.get_json() or {}`, `@handle_route_exceptions`. Do not validate or alter payloads in the route.

Shared `EventService.create_event` returns the **document**. POST `/api/event` should return that document with `201` (do not assume a bare id). Resource/Path/Plan/Encounter create may still return an id from the local method — keep the existing create-then-GET-by-id `201` pattern for those.

**Drop** `_paginated_response` helpers and every `X-Pagination-*` header on Resource/Path/Plan/Event lists. Factories already return `jsonify(array), 200`.

**Profile factory vs dashboard:** `create_profile_get_routes` calls `get_profiles(token, breadcrumb, offset, size, filters, sort_by)`. F346’s override ignores the extra args. OpenAPI stays non-paginated dashboard cards. Update `test/routes/test_profile_routes.py` if `parse_list_request` now 400s on query params the old handler ignored.

There is **no** Journey HTTP blueprint. Do **not** mount `create_journey_get_routes`. Do **not** mount aggregation factories (separate pending L310/L330 chain; out of scope).

## Goals

- `Pipfile` and `Pipfile.lock` pin `api-utils==1.0.0` (CodeArtifact `[[source]]` unchanged; keep the comment that public PyPI `api-utils` is unrelated).
- Every `src/routes/*_routes.py` imports its service from `src.services.*`. Zero `from api_utils.services import *Service` in `src/routes/` (filter/order constants from api_utils are allowed only if a factory needs them; prefer MRO lookup).
- Shared GET factories used where specified; dashboard, Properties hub, Event by-id, and control POST/PATCH stay local on those blueprints.
- List GETs have **no** `X-Pagination-*` response headers.
- `README.md` states the `api-utils==1.0.0` pin, that `src/services/` subclasses shared classes, and that routes import those subclasses (JSON-array list GETs, `offset`/`size` headers).
- Route unit tests keep patching `src.routes.<module>.<Service>.*`. Remove pagination-header assertions. Add encounter list GET tests. Dashboard and control POST/PATCH tests still pass.
- E2E covers list GETs without `X-Pagination-*`, encounter list, dashboard enrich, and existing control flows.

## Testing Expectations

Run all commands from this API repository root.

- **Install**
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `pipenv run install`
  - Confirm `importlib.metadata.version("api-utils") == "1.0.0"`
- **Confirmation greps** (zero hits in `src/routes/`)
  - `rg "from api_utils.services import .+Service" src/routes`
  - `rg "X-Pagination-" src/routes test/`
- **Unit / lint / build**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Dev E2E**
  - `pipenv run db` if needed
  - `pipenv run dev` (separate terminal or background)
  - `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e` against the containerized API
  - `curl -s http://localhost:8391/docs/openapi.yaml` — includes F340 list contract; no list `X-Pagination-*`; dashboard / `ProfileDetail` remain

## Outputs

- `Pipfile` — pin `api-utils==1.0.0`
- `Pipfile.lock` — refresh via `pipenv run install` (use `scripts/pipenv-lock.sh` if hashes must be regenerated first)
- `README.md` — 1.0.0 pin, local subclasses, list GET contract (no `X-Pagination-*`)
- `src/routes/resource_routes.py`
- `src/routes/path_routes.py`
- `src/routes/plan_routes.py`
- `src/routes/profile_routes.py`
- `src/routes/mentee_routes.py`
- `src/routes/encounter_routes.py`
- `src/routes/event_routes.py`
- `src/routes/__init__.py` — only if exports are needed
- `src/server.py` — only if blueprint constructors or log lines must change
- `test/routes/test_resource_routes.py`
- `test/routes/test_path_routes.py`
- `test/routes/test_plan_routes.py`
- `test/routes/test_profile_routes.py`
- `test/routes/test_mentee_routes.py`
- `test/routes/test_encounter_routes.py`
- `test/routes/test_event_routes.py`
- `test/test_server.py` — only if URL-rule assertions need updates (new `GET /api/encounter` list)
- `test/e2e/test_resource.py` — drop `X-Pagination-*` assertions
- `test/e2e/test_path.py` — drop `X-Pagination-*` if present
- `test/e2e/test_plan.py` — drop `X-Pagination-*` if present
- `test/e2e/test_event.py` — drop `X-Pagination-*` assertions
- `test/e2e/test_encounter.py` — add list GET with required `mentee_id`
- `test/e2e/test_profile.py` — dashboard / detail / properties still pass
- `test/e2e/e2e_auth.py` — only if `profile_id` is missing

The agent must not update files outside this list.

## Execution Notes
