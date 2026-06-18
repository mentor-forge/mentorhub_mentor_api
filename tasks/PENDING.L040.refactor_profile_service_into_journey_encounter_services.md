# L040 – Refactor profile_service into Journey and Encounter services

**Status**: Pending  
**Type**: Feature  
**Depends On**: L030  
**Description**: Clean up `profile_service.py` by extracting domain logic into dedicated services: move the learning-journey aggregation into a new `JourneyService` and the encounter logic into the existing `EncounterService`. `ProfileService` should then compose its dashboard (`get_profiles`) and detail (`get_profile`) responses via **service-to-service** calls rather than holding all of this logic itself. This is a behavior-preserving refactor.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml`

Pattern references:

- `src/services/profile_service.py` — currently holds `_journey_progress` (journey aggregation) and `_recent_encounter` (encounter summary), used by `get_profiles` and `get_profile`
- `src/services/encounter_service.py` — destination for encounter logic
- other `src/services/*_service.py` — service shape/conventions to mirror for the new `JourneyService`

## Goals

- New `src/services/journey_service.py` (`JourneyService`) owns journey logic currently in `ProfileService._journey_progress` (active-journey resource counts by scope: library / now / next).
- `EncounterService` owns the encounter logic currently in `ProfileService._recent_encounter` (most-recent encounter summary) and exposes the per-mentee encounter reads used by L030.
- `ProfileService.get_profiles` and `ProfileService.get_profile` call `JourneyService` and `EncounterService` (service-to-service); the private `_journey_progress` / `_recent_encounter` helpers are removed from `ProfileService`.
- No behavior change: the dashboard and detail responses are identical to before the refactor.
- No circular imports.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - New `test/services/test_journey_service.py` for the extracted journey logic.
  - Update `test/services/test_encounter_service.py` for the moved/added encounter logic.
  - Update `test/services/test_profile_service.py` to mock `JourneyService`/`EncounterService` and assert delegation (responses unchanged).
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - Existing `test/e2e/test_profile.py` (dashboard + detail) still passes unchanged.
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API.

## Outputs

Paths are relative to the **API repository root**.

- `src/services/journey_service.py` — new `JourneyService`
- `src/services/encounter_service.py` — house the recent-encounter logic / per-mentee reads
- `src/services/profile_service.py` — delegate to `JourneyService`/`EncounterService`; remove `_journey_progress` and `_recent_encounter`
- `test/services/test_journey_service.py` — new unit tests
- `test/services/test_encounter_service.py` — updated unit tests
- `test/services/test_profile_service.py` — updated to assert delegation

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
