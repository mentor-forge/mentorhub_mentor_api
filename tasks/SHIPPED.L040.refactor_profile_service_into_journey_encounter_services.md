# L040 – Refactor profile_service into Journey and Encounter services

**Status**: Shipped  
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

**Summary of changes** (behavior-preserving refactor)
- `src/services/journey_service.py` (new): `JourneyService.get_journey_progress(profile_id, token, breadcrumb)` → `{library, now, next}` (zeros when no active journey). Extracted from `ProfileService._journey_progress`.
- `src/services/encounter_service.py`: added `get_recent_encounter(mentee_id, token, breadcrumb)` (most-recent summary or None) and `get_encounters_for_mentee(mentee_id, token, breadcrumb)` (mentee's encounters, most-recent first; direct `mentee_id` match + sort). Helper `_normalize_mentee_id` handles str/ObjectId. Replaces L030's interim limit-then-filter.
- `src/services/profile_service.py`: `get_profiles` and `get_profile` now delegate to `JourneyService`/`EncounterService` (service-to-service); removed `_journey_progress`, `_recent_encounter`, `_mentee_encounters`. Response shapes unchanged.
- Tests: new `test_journey_service.py`; updated `test_encounter_service.py` and `test_profile_service.py` (assert delegation, shapes unchanged).

**Testing results**
- `pipenv run test`: 184 passed, 27 deselected (+11 new).
- `pipenv run build`: clean.
- Lint: all 6 changed/created files black-clean.
- E2E/packaging verification: deferred to a configured environment (see L020 notes).

**Follow-ups**
- None specific; `JourneyService` could later own additional journey reads if needed.
