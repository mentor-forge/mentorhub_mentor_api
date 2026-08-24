# F345 – JourneyService and EventService subclasses

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F344_mentee_service_subclass`  
**Description:** `JourneyService` subclasses the shared class and **deletes** the local `get_journey_progress` duplicate (now upstream). Do not add Mentee Journey mutations. `EventService` inherits `create_event` / `get_events`; drop the local `create_event` duplicate and prefer `super().create_event`. Keep local `get_event` (shared 1.0.0 has no by-id). Event create is any authenticated user. Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **creates** Event; **consumes** Profile; does **not** control Journey (Mentee does)
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; do not 403 on GET
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — 1.0.0 parent: `get_journey`, `get_journey_progress` (zeros when missing or not visible); no mutations
- `../mentorhub_api_utils/api_utils/services/event_service.py` — shared `create_event` (stamps `context` from the token, encodes ids, returns the **document**); `get_events`; `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`; no `get_event`
- `src/services/journey_service.py` — standalone `@staticmethod` progress aggregation that 403s non-mentors on read
- `src/services/event_service.py` — composes `SharedEventService.get_events`; local `create_event` returns an **id** and encodes `profile_id`; local `get_event`
- `src/services/profile_service.py` — calls `JourneyService.get_journey_progress` (must keep importing `src.services.journey_service`)
- `test/services/test_journey_service.py`
- `test/services/test_event_service.py`

**MongoDB I/O:** Prefer inherited shared methods. Local `get_event` uses `MongoIO.get_document`. Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`. This API has **no** Journey HTTP routes — do not add them.

### Journey

```python
from api_utils.services import JourneyService as SharedJourneyService

class JourneyService(SharedJourneyService):
    """Mentor consume: inherit get_journey_progress. No Journey mutations."""
```

Delete the local `get_journey_progress` body and the local `_check_permission` that 403s on GET. Do **not** port clone-on-GET, PATCH, promote, advance, or complete (Mentee **controls** Journey).

Unit tests that mocked local MongoIO for progress should mock `super().get_journey_progress` (or call the subclass and mock parent I/O) so they pass on installed `api-utils==0.5.1`, which may not yet expose this method.

### Event

```python
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
