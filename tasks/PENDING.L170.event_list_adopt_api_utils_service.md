# L170 – Event list: adopt shared api_utils EventService

**Status**: Pending  
**Type**: Feature  
**Depends On**: L160_resource_list_adopt_api_utils_service  
**Description**: Replace the local Event **list** path with the harvested shared service. Delete the local `EventService.get_events` list implementation and use `api_utils.services.EventService.get_events` with `offset`/`size` request headers, `type`/`profile_id` filter query params, and standardized `sort_by`/`order` per the shared `EVENT_LIST_ORDER` order spec. Keep the local `get_event` (by-id) and `create_event` until Event is separately harvested. Update `src/routes/event_routes.py` and `docs/openapi.yaml`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/event_service.py`
- `src/routes/event_routes.py`
- `docs/openapi.yaml` (Event paths + schemas)
- `test/services/test_event_service.py`
- `test/routes/test_event_routes.py`
- `test/e2e/test_event.py`

**Shared service contract (api_utils 0.5.0)**

- Inspect `api_utils.services.EventService.get_events` for the exact signature, the `EVENT_LIST_ORDER` order spec, supported filters (`type`, `profile_id`), and offset/size header handling. Follow that contract exactly; record the resolved signature in **Execution Notes**.

**Current state**

- `EventService.get_events(token, breadcrumb)` is a full-list read sorted by `created.at_time` asc via `MongoIO.get_documents`, with no filters. `create_event` encodes `_id`/`profile_id` to BSON ObjectId (`ID_PROPERTIES`) before insert; `get_event` reads a single document by id. Keep both local for now.

**MongoIO rule**

- Retained local `get_event` / `create_event` must route all MongoDB I/O through `MongoIO` (no direct PyMongo). Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- The local Event **list** logic is removed; `GET /api/event` is served by `api_utils.services.EventService.get_events`.
- `GET /api/event` accepts:
  - `offset`/`size` **request headers** for pagination.
  - `type` and `profile_id` filter query params.
  - Standardized `sort_by`/`order` query params validated per `EVENT_LIST_ORDER`.
- Local `get_event` (by-id) and `create_event` remain unchanged (including ObjectId encoding of `profile_id`).
- Response is a plain array; pagination metadata conveyed via response headers per the shared contract.
- Unit and E2E tests for Event pass.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev`
  - `pipenv run e2e`
  - Manual check: `curl -sD - "http://localhost:8391/api/event?type=login&sort_by=created.at_time&order=desc" -H "Authorization: Bearer $TOKEN" -H "offset: 0" -H "size: 10"`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/event_service.py` — remove local list logic; delegate list reads to `api_utils.services.EventService.get_events`; keep local `get_event` and `create_event`
- `src/routes/event_routes.py` — `GET /api/event` uses offset/size headers + `type`/`profile_id` filters + `sort_by`/`order`
- `docs/openapi.yaml` — Event `GET /api/event` operation: header pagination + filter/order query params (central schema cleanup in L220)
- `test/services/test_event_service.py` — update for delegated list + retained by-id/create
- `test/routes/test_event_routes.py` — update for header pagination + filters
- `test/e2e/test_event.py` — update expectations (array response + pagination headers + filters)

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
