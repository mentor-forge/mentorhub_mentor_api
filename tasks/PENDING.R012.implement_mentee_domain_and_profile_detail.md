# R012 – Implement Mentee domain + Profile detail view

**Status**: Pending  
**Task Type**: Feature  
**Run Mode**: Sequential  <!-- options: Sequential | Run as needed -->

## Goal

Implement the API described in R011:

- A new Mentee domain (`/api/mentee`) with a `MenteeService` that owns the
  mentee-notes document (read-with-create-if-missing + update).
- `GET /api/profile/{ProfileId}` returns the composite mentee detail view
  (Profile + mentee notes + Encounters), assembled via **service-to-service**
  calls rather than direct cross-domain Mongo access.

## Context / Input files

These files must be treated as **inputs** and read before implementation:

- `mentorhub_mentor_api/docs/openapi.yaml` – the contract from R011
- `mentorhub_mentor_api/src/services/encounter_service.py` – service/MongoIO pattern
- `mentorhub_mentor_api/src/routes/encounter_routes.py` – route/blueprint pattern
- `mentorhub_mentor_api/src/services/profile_service.py` – `get_profile` to enrich
- `mentorhub_mentor_api/src/server.py` – blueprint registration
- `mentorhub_mongodb_api/configurator/dictionaries/Note.0.1.0.yaml` – backing schema

## Requirements

- **`src/services/mentee_service.py`** (`MenteeService`)
  - `get_mentee(profile_id, token, breadcrumb)` – return the `Note`-backed
    mentee-notes doc for `profile_id`; create a default if none exists.
  - `update_mentee(mentee_id, data, token, breadcrumb)` – update; reject `_id`,
    `created`, `saved`; set `saved` from breadcrumb; `404` if missing.
  - RBAC: `mentor` or `admin` via `Config.MENTOR_ROLE` / `Config.ADMIN_ROLE`.
- **`src/routes/mentee_routes.py`** – `GET /<profile_id>`, `PATCH /<mentee_id>`,
  using `create_flask_token`, `create_flask_breadcrumb`, `@handle_route_exceptions`.
- **`src/server.py`** – register blueprint at `url_prefix='/api/mentee'`.
- **`src/services/encounter_service.py`** – add
  `get_encounters_for_mentee(mentee_id, token, breadcrumb)` (sorted by date desc).
- **`src/services/profile_service.py`** – `get_profile` returns
  `{profile, notes, encounters}`; `notes` from `MenteeService.get_mentee`,
  `encounters` from `EncounterService.get_encounters_for_mentee` (service-to-service).
- Avoid circular imports (`profile → mentee`/`encounter` only).

## Testing expectations

- **Unit tests**
  - `test/services/test_mentee_service.py` – get (existing + create-if-missing),
    update, RBAC allow/deny, restricted-field rejection.
  - `test/routes/test_mentee_routes.py` – GET/PATCH success + forbidden.
  - Update `test/services/test_profile_service.py` – `get_profile` composite,
    mocking `MenteeService`/`EncounterService` to assert service-to-service calls.
- **End-to-end (e2e) tests**
  - `test/e2e/test_mentee.py` – GET (auto-create) then PATCH round-trip.
  - Extend `test/e2e/test_profile.py` – assert composite `{profile, notes, encounters}`.
  - Run with `pipenv run e2e` against a running API at `localhost:8391`.

## Packaging / build checks

- `pipenv run test` (unit) green.
- `pipenv run lint` clean.
- `pipenv run container` (or `make container`) builds successfully.

## Dependencies / Ordering

- Should run **after**: `R011` (OpenAPI contract).
- Related to `R010`: relies on the shared `Config` role constants (mentor/admin)
  already present on `dashboard-refactor`.
- Branch: `dashboard-refactor` (mentor_api).
- Coordinate with Mary: if a dedicated `Mentee` collection/schema replaces the
  `Note`-backed store, only `MenteeService` should need changes.

## Change control checklist

- [ ] Reviewed all **Context / Input files** (including the R011 contract).
- [ ] Implemented `MenteeService` + `mentee_routes` + server registration.
- [ ] Added `EncounterService.get_encounters_for_mentee`.
- [ ] Updated `ProfileService.get_profile` to the composite via service-to-service calls.
- [ ] Added/updated **unit tests**.
- [ ] Added/updated **e2e tests**.
- [ ] Ran unit tests and e2e tests; all passing.
- [ ] Ran packaging/build steps; build successful.
- [ ] Created scoped commit(s) referencing this task ID.

## Implementation notes (to be updated by the agent)

**Summary of changes**
- _TBD_

**Testing results**
- Unit tests: _command(s) run, high-level outcome_
- E2E tests: _command(s) run, high-level outcome_
- Packaging/build: _command(s) run, high-level outcome_

**Follow-up tasks**
- _Swap `Note` for a dedicated Mentee collection if/when Mary publishes one._
