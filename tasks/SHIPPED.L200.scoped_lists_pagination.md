# L200 – Scoped lists: encounter-by-mentee pagination and dashboard read decision

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L190_plan_list_header_pagination  
**Description**: Bring the two **scoped** list reads in line with the pagination conventions. (1) `EncounterService.get_encounters_for_mentee` should support `offset`/`size` pagination **within the `mentee_id` scope** (still sorted by `date` desc). (2) `ProfileService.get_profiles` (Mentor Dashboard) should be evaluated for pagination over mentee cards; either add pagination or explicitly document the intentional full read. Encounter and Profile remain mentor-only local domains.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/encounter_service.py`
- `src/services/profile_service.py`
- `src/routes/encounter_routes.py`
- `src/routes/profile_routes.py`
- `docs/openapi.yaml` (Encounter + Profile paths/schemas)
- `test/services/test_encounter_service.py`
- `test/services/test_profile_service.py`
- `test/e2e/test_encounter.py`
- `test/e2e/test_profile.py`

**Pagination/order convention (api_utils 0.5.0)**

- Reuse the offset/size header + `sort_by`/`order` helpers adopted in L160–L190. Record the helpers used in **Execution Notes**.

**Current state**

- `EncounterService.get_encounters_for_mentee(mentee_id, token, breadcrumb)` returns **all** of a mentee's encounters, sorted by `date` desc, via a direct `MongoIO.get_documents` match on `mentee_id`. It is consumed by the Profile detail composite (`ProfileService.get_profile`) and by `get_profile_properties`.
- `ProfileService.get_profiles(token, breadcrumb)` builds the Mentor Dashboard: one card per assigned mentee (Profiles whose `mentor_id` matches the caller), sorted by `name` asc. It is documented today as read-only and **non-paginated** and takes no parameters.
- Both are **service-to-service** consumers as well as route-backed reads, so pagination params must be **optional** and default to current behavior to avoid breaking composite callers (`get_profile`, `get_profile_properties`) that expect the full encounter list.

**MongoIO rule**

- Both domains stay local: route all MongoDB I/O through `MongoIO` (no direct PyMongo). Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- `EncounterService.get_encounters_for_mentee` accepts **optional** `offset`/`size` pagination scoped to the given `mentee_id`, preserving `date` desc ordering; when pagination args are omitted it returns the full list so existing composite callers are unaffected.
- The mentee-scoped encounter route (if it exposes this read) parses offset/size headers and emits pagination headers per the shared contract.
- A decision is made and implemented for `ProfileService.get_profiles`:
  - **Either** add optional `offset`/`size` pagination over the mentee cards (with pagination response headers on `GET /api/profile`), **or**
  - Explicitly document the intentional full read (docstring + OpenAPI description) with the rationale (bounded per-mentor cohort).
- Composite callers `ProfileService.get_profile` and `get_profile_properties` continue to receive the complete encounter list.
- Unit and E2E tests for Encounter and Profile pass.

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
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/encounter_service.py` — `get_encounters_for_mentee` gains optional offset/size pagination within mentee scope (default = full list)
- `src/services/profile_service.py` — `get_profiles` either gains optional pagination or documents the intentional full read; composite callers unchanged in behavior
- `src/routes/encounter_routes.py` — parse offset/size headers + emit pagination headers where the mentee-scoped encounter read is exposed
- `src/routes/profile_routes.py` — apply pagination headers on `GET /api/profile` only if pagination is adopted
- `docs/openapi.yaml` — update Encounter (mentee-scoped) and Profile dashboard operations to reflect the chosen pagination/no-pagination contract
- `test/services/test_encounter_service.py` — cover scoped pagination + default full-list behavior
- `test/services/test_profile_service.py` — cover the chosen dashboard behavior
- `test/e2e/test_encounter.py` — update expectations
- `test/e2e/test_profile.py` — update expectations

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
