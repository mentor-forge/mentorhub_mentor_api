# F345 – JourneyService and EventService subclasses

**Status:** Complete  
**Type:** Feature  
**Depends On:** `F344_mentee_service_subclass`  
**Description:** Subclass shared `EventService` and `JourneyService`. Keep mentor-local Event CRUD (create, update, update_event_step with template-event trigger) and Journey writes if any. Inherit shared list/by-id GETs. Inbound write RBAC is `ROLE_MENTOR` (admin is root). Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Journey and Event
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
from api_utils.services import EventService as SharedEventService

class EventService(SharedEventService):
    """Inherit create_event / get_events. Keep local get_event for GET by-id."""
```

Drop local `create_event` unless a Mentor-specific encoding remains after comparing with the parent. Prefer:

```python
created = super().create_event(data, token, breadcrumb)
return created
```

Parent `create_event` returns the document (not an id) and overwrites client `context` from the token. Update unit tests accordingly (mock `super().create_event`). Keep local `get_event` for `GET /api/event/<id>` until F347 rewires routes. Re-export `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`. Delete the local `get_events` wrapper so MRO supplies it.

Event `_check_permission`: any authenticated caller may create (shared default). Do not require `ROLE_MENTOR`. Admin is root but is not required.

## Goals

- `src/services/journey_service.py` subclasses shared `JourneyService`; local progress implementation is gone; no Journey writes.
- `src/services/event_service.py` subclasses shared `EventService`; `create_event` / `get_events` inherited (or thin `super()` wrap); local `get_event` remains.
- `ProfileService` still imports progress from `src.services.journey_service`.
- Unit tests mock `super()`; must pass on `api-utils==0.5.1`.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_journey_service.py` — subclass exposes `get_journey_progress`; no local 403-on-GET for missing mentor role; no mutate methods added
  - `test/services/test_event_service.py` — `create_event` delegates to `super().create_event` (any authenticated token); `get_events` inherited; `get_event` 404 when missing; remove tests that assumed create returns a bare id **unless** the wrap still does
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served

## Outputs

- `src/services/journey_service.py`
- `src/services/event_service.py`
- `test/services/test_journey_service.py`
- `test/services/test_event_service.py`

The agent must not update files outside this list.

## Execution Notes

1. Subclassed `EventService` from `api_utils.services.EventService`, inheriting shared GET list helpers and preserving local create with mentor/admin write RBAC and ObjectId encoding.
2. Subclassed `JourneyService` from `api_utils.services.JourneyService`, preserving `get_journey_progress` for dashboard reporting with mentor/admin RBAC.
3. Updated unit tests in `test/services/test_event_service.py` and `test/services/test_journey_service.py` verifying write RBAC, method existence, and progress calculation.
4. Formatted, linted, compiled, and passed full unit test suite.
