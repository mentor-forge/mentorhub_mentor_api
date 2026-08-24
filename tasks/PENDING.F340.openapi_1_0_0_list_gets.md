# F340 – OpenAPI for 1.0.0 list GETs (drop `X-Pagination-*`)

**Status:** Pending  
**Type:** Feature  
**Depends On:** none  
**Description:** First task of F-RA13 (this repo’s only 1.0.0-wave issue; same PR as F341–F347). Document the 1.0.0 list GET contract that `create_*_get_routes` factories will mount in F347: JSON-array bodies, `offset`/`size` request headers only, no pagination response headers. Keep Mentor Dashboard, `ProfileDetail`, Properties hub, Event by-id, and all control POST/PATCH. No Python in this task. The `api-utils==1.0.0` pin is F347 so current `==0.5.1` routes stay green until subclasses exist.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Resource, Path, Plan, Encounter; **creates** Event; **consumes** Profile
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — OpenAPI is the SPA contract
- `tasks/_PLANNING.md` — fetch schemas from the running configurator only when component schemas change
- `README.md`
- `../mentorhub_api_utils/README.md` — list GET is a JSON **array**; pagination is request headers `offset` (default `0`) and `size` (default `20`, max `100`); query `contains` / `in_list` plus `sort_by` / `order`; no cursor envelope; no pagination response headers
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — factory URL shapes: resource/path/plan/profile list + by-id; event list only; mentee by profile_id; encounter list requires `mentee_id` plus by-id
- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `RESOURCE_LIST_FILTERS` / `RESOURCE_LIST_ORDER`
- `../mentorhub_api_utils/api_utils/services/path_service.py` — `PATH_LIST_FILTERS` / `PATH_LIST_ORDER`
- `../mentorhub_api_utils/api_utils/services/plan_service.py` — `PLAN_LIST_FILTERS` / `PLAN_LIST_ORDER`
- `../mentorhub_api_utils/api_utils/services/event_service.py` — `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`
- `docs/openapi.yaml` — current spec still documents `X-Pagination-*` on Resource/Path/Plan/Event lists; Profile list is Mentor Dashboard cards (`MentorDashboardProfile`); Profile by-id is `ProfileDetail`; Properties hub is local
- `../mentorhub/Specifications/architecture.yaml` — Mentor controls Resource / Path / Plan / Encounter; creates Event; consumes Profile

**Do not change these existing operations** (HTTP contract stays; only list-GET pagination *response* headers are removed where listed below):

| Method and path | Keep |
| --- | --- |
| `POST` / `PATCH` `/api/resource`, `/api/path`, `/api/plan`, `/api/encounter` | control writes |
| `PATCH /api/mentee/{mentee_id}` | mentee notes update |
| `POST /api/event` | Event create |
| `GET /api/event/{EventId}` | local by-id (factory is list-only) |
| `GET /api/profile` | Mentor Dashboard cards (`MentorDashboardProfile[]`), non-paginated |
| `GET /api/profile/{ProfileId}` | `ProfileDetail` `{profile, mentee, encounters}` |
| `GET /api/profile/{ProfileId}/properties` | Properties hub aggregate |
| `GET /api/mentee/{profile_id}` | create-if-missing mentee notes |

**Update these list GETs** — keep `offset`/`size` **request** headers and JSON-array `200` bodies; **delete** `X-Pagination-Offset` / `X-Pagination-Size` / `X-Pagination-Returned` from the `200` response:

| Method and path | Body out |
| --- | --- |
| `GET /api/resource` | `Resource[]` |
| `GET /api/path` | `Path[]` |
| `GET /api/plan` | `Plan[]` |
| `GET /api/event` | `Event[]` |

**Add this operation** (encounter factory in F347; not on the current spec):

| Method and path | Body out | Notes |
| --- | --- | --- |
| `GET /api/encounter` | `Encounter[]` | required query `mentee_id`; `offset`/`size` request headers; no `X-Pagination-*` |

Do **not** add Journey, Note, Rating, Aggregation, Customer, or Profile POST/PATCH paths. Customer **controls** Profile. Do **not** document a paginated plain-Profile list on `GET /api/profile` — that path stays dashboard cards.

If a component schema is missing a field the live dictionary has, fetch from the running configurator (`pipenv run db` first):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Path.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Plan.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Encounter.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

If this task only edits paths that reuse **existing** components, do not Block on the configurator.

## Goals

- Resource, Path, Plan, and Event list GETs keep `offset`/`size` request headers (defaults `0` / `20`, max `100`), `contains` / `in_list` filters, and `sort_by` / `order` from the shared list specs. `200` body remains a JSON **array**.
- Those four list operations no longer declare `X-Pagination-*` response headers. Remove unused `components.headers` entries for `X-Pagination-Offset` / `X-Pagination-Size` / `X-Pagination-Returned` if nothing else references them.
- No `after_id`, `has_more`, `next_cursor`, or cursor envelope anywhere in this document.
- `GET /api/encounter` is documented as a mentee-scoped list (required `mentee_id`, `offset`/`size` request headers, `Encounter[]`). Existing POST on `/api/encounter` and GET/PATCH by-id stay.
- `GET /api/profile` remains Mentor Dashboard (`MentorDashboardProfile[]`), non-paginated, no filter/sort/pagination parameters.
- `GET /api/profile/{ProfileId}` remains `ProfileDetail`. Properties hub stays.
- Event by-id GET stays (factory does not mount it).
- The document remains valid OpenAPI 3.0.x.
- No Python, Pipfile, or README changes.

## Testing Expectations

Run all commands from this API repository root.

- **Spec validation**
  - `python3 -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - Confirm Resource/Path/Plan/Event list `200` responses have no `X-Pagination-*`; `offset`/`size` request headers remain; `GET /api/encounter` list exists; dashboard / `ProfileDetail` / Properties / Event by-id / control POST/PATCH are unchanged.
- **Unit / lint / build** (docs-only; suite must still pass on `api-utils==0.5.1`)
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — served file drops list `X-Pagination-*`, adds encounter list GET, and keeps dashboard / control paths

## Outputs

- `docs/openapi.yaml` — drop list `X-Pagination-*`; add `GET /api/encounter`; keep dashboard, `ProfileDetail`, Properties, Event by-id, and control writes

The agent must not update files outside this list.

## Execution Notes
