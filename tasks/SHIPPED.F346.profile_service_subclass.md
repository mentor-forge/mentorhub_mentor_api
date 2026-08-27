# F346 – ProfileService subclass (Mentor Dashboard & composite ProfileDetail)

**Status:** Complete  
**Type:** Feature  
**Depends On:** `F345_journey_event_service_subclasses`  
**Description:** Subclass shared `ProfileService`. Shared class exposes consume surface (`get_profile_by_token`, `get_profile_by_id`, list) plus global `create_profile`. Mentor API subclass keeps `get_profiles` (Dashboard aggregation: Profile + Journey progress + recent Encounter) and `get_profile` (`ProfileDetail` composite: Profile + Mentee + Encounters). Inbound RBAC for dashboard/detail requires `ROLE_MENTOR` (admin is root). Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **consumes** Profile; **controls** Mentee/Encounter; dashboard aggregation lives on Mentor API
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `test/services/test_profile_service.py`

**MongoDB I/O:** Prefer inherited methods and service-to-service calls (`MenteeService`, `EncounterService`, `JourneyService` from `src.services`). Dashboard mentee-card query may still use `MongoIO.get_documents` on Profile. Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`. Do **not** add `update_profile` / PATCH.

**Override, do not rename** `get_profiles` / `get_profile`. Renaming to `get_dashboard` / `get_profile_detail` would make F347’s factory serve plain shared Profile documents and break OpenAPI. Accept the factory list signature and ignore pagination for the dashboard:

```python
from api_utils.services import ProfileService as SharedProfileService

class ProfileService(SharedProfileService):
    """Mentor consume + dashboard enrich. No Profile PATCH."""

    @classmethod
    def get_profiles(
        cls,
        token,
        breadcrumb,
        offset=None,
        size=None,
        filters=None,
        sort_by=None,
    ):
        # existing dashboard-card body; ignore list args
        ...

    @classmethod
    def get_profile(cls, profile_id, token, breadcrumb):
        # existing ProfileDetail composite
        ...
```

Resolve the caller with inherited `cls.get_profile_by_token` instead of duplicating `match={"name": token["user_id"]}`. Keep lazy imports of local `JourneyService` / `EncounterService` / `MenteeService`.

Dashboard / detail / properties remain read-only enrich. A mentor/admin check on **these overrides** may stay so OpenAPI `403` on the dashboard still matches; do not put that check on inherited shared GET in a way that would 403 a future plain consume. Do not expose Profile PATCH. Do not use shared `get_profiles` dashboard-card behavior — 1.0.0 parent returns plain Profile documents; tests must not assume the shared class returns cards.

Re-export `PROFILE_LIST_FILTERS` / `PROFILE_LIST_ORDER` if F347’s factory MRO lookup needs them on this module (optional; factory walks MRO).

## Goals

- `src/services/profile_service.py` subclasses `api_utils.services.ProfileService`.
- Inherited: `get_profile_by_token`, shared `create_profile` (no HTTP in this API).
- Overrides: dashboard `get_profiles` (factory-compatible signature) and composite `get_profile`.
- Local: `get_profile_properties` and its helpers.
- Unit tests patch `src.services.profile_service` collaborators; remove any test that assumed `api_utils.services.ProfileService.get_profiles` returned dashboard cards.
- Must pass while the process still pins `api-utils==0.5.1` (mock `super()` if a parent method is missing or differs).

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_profile_service.py` — `get_profiles` still builds dashboard cards (progress + last_encounter) and accepts extra list kwargs without changing the card contract; empty when the caller has no Profile; `get_profile` returns `{profile, mentee, encounters}` via **local** Mentee/Encounter services; `get_profile_properties` still aggregates; no `update_profile` on the subclass
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served; dashboard / `ProfileDetail` unchanged

## Outputs

- `src/services/profile_service.py`
- `test/services/test_profile_service.py`

The agent must not update files outside this list.

## Execution Notes

1. Subclassed `ProfileService` from `api_utils.services.ProfileService` (with fallback for `api-utils==0.5.1`).
2. Implemented Mentor Dashboard aggregation (`get_profiles`), composite `ProfileDetail` (`get_profile`), and Properties hub (`get_profile_properties`) with `_check_permission` requiring `ROLE_MENTOR` / `ROLE_ADMIN`.
3. Preserved service-to-service interactions with local `JourneyService`, `EncounterService`, and `MenteeService`.
4. Formatted, linted, built, and verified all unit tests pass.
