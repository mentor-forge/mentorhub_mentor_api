# L030 – Update Profile service to return the composite detail view

**Status**: Pending  
**Type**: Feature  
**Depends On**: L020  
**Description**: Update `ProfileService.get_profile` so `GET /api/profile/{_id}` returns the composite detail view from L010 — the `Profile` plus the related mentee notes and the mentee's `Encounter` list. Assemble it with **service-to-service** calls (the profile service calls `MenteeService.get_mentee` and the encounter service), not direct cross-collection MongoDB access. The aggregation should resemble the `get_profiles` dashboard method already in this service.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml` (the `ProfileDetail` contract from L010)

Pattern references:

- `src/services/profile_service.py` — current `get_profile` and the `get_profiles` dashboard aggregation (model the composition on it)
- `src/services/mentee_service.py` — `get_mentee` (from L020)
- `src/services/encounter_service.py` — encounter reads for a mentee

## Goals

- `ProfileService.get_profile(profile_id, token, breadcrumb)` returns a composite document: `{ profile, mentee, encounters }`.
  - `profile` — the `Profile` document (`404` if not found).
  - `mentee` — from `MenteeService.get_mentee(profile_id, ...)` (create-if-missing applies).
  - `encounters` — the mentee's encounters from the encounter service (sorted by date, most recent first).
- Cross-collection data is fetched **only** through other services (service-to-service); `profile_service` does not query the Note/Mentee or Encounter collections directly.
- No circular imports (`profile` depends on `mentee`/`encounter`, not the reverse).
- Response matches the L010 `ProfileDetail` contract.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - Update `test/services/test_profile_service.py`: `get_profile` returns the composite; mock `MenteeService` and the encounter service to assert the service-to-service calls (no direct cross-collection access).
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - Extend `test/e2e/test_profile.py`: assert `GET /api/profile/{id}` returns `{ profile, mentee, encounters }`.
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API.

## Outputs

Paths are relative to the **API repository root**.

- `src/services/profile_service.py` — `get_profile` returns the composite via service-to-service calls
- `test/services/test_profile_service.py` — updated unit tests for the composite
- `test/e2e/test_profile.py` — extended e2e assertion for the composite response

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
