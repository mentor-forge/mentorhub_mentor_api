# F353 – Schedule Encounters mutation

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F352_patch_encounter_active_restrictions`  
**Description:** Implement the Schedule Encounters mutation. Add `schedule_encounters` in `EncounterService` and route `POST /api/encounter/schedule`. Accepts `mentor_id`, `mentee_id`, `plan_id`, `start_date`, `day_of_week`, `time_of_day`, `recurrence_days`, and `count`. Generates `count` encounter documents with `status: "scheduled"`, calculated `appointment: { from, to }` intervals, auto-filled agenda from the referenced Plan's checklist, saves documents via `MongoIO.create_document`, and returns the enriched encounter documents.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Route is HTTP only; Business logic and RBAC in Service layer
- `tasks/_PLANNING.md` — MongoIO only; encode ids at boundary
- `README.md`
- `docs/openapi.yaml` — `POST /api/encounter/schedule` and `ScheduleEncounterInput` schema
- `src/services/encounter_service.py` — `schedule_encounters` implementation
- `src/services/plan_service.py` — Plan retrieval for agenda derivation
- `src/routes/encounter_routes.py` — mount `POST /api/encounter/schedule`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

## Goals

- In `src/services/encounter_service.py`:
  - Add `schedule_encounters(cls, data, token, breadcrumb)`:
    - Inbound RBAC check: caller must have `ROLE_ADMIN`, or `ROLE_MENTOR` where caller's Profile `_id` matches `data["mentor_id"]`. Otherwise raise `HTTPForbidden`.
    - Validate required parameters:
      - `mentor_id`, `mentee_id`, `plan_id`, `start_date`, `time_of_day`, `count` are required.
      - Support `day_of_week` (or `day-of-week`), defaulting to start_date's day of week if omitted.
      - Support `recurrence_days`, defaulting to `7` if omitted.
      - Validate `count`: integer >= 1 (e.g. up to 52).
    - Retrieve plan via `PlanService.get_plan(data["plan_id"], token, breadcrumb)`.
    - Derive initial agenda from plan steps/checklist via `cls._build_agenda_from_plan(plan)`.
    - Appointment scheduling calculation:
      - Parse `start_date` and `time_of_day`.
      - Calculate recurring appointment times for `count` encounters:
        - First occurrence begins at `start_date` / `time_of_day` adjusted to match `day_of_week`.
        - Subsequent occurrences advance by `recurrence_days` intervals.
        - Appointment duration defaults to 1 hour (e.g. `to = from + timedelta(hours=1)`).
        - Format `appointment.from` and `appointment.to` as ISO 8601 strings (`YYYY-MM-DDTHH:MM:SSZ`).
    - Document creation:
      - For each of the `count` encounters, prepare:
        ```python
        doc = {
            "mentor_id": data["mentor_id"],
            "mentee_id": data["mentee_id"],
            "plan_id": data["plan_id"],
            "status": "scheduled",
            "appointment": {"from": from_time_iso, "to": to_time_iso},
            "agenda": list(agenda),
            "created": breadcrumb,
            "saved": breadcrumb,
        }
        ```
      - Encode ObjectIds via `encode_document(doc, ["mentor_id", "mentee_id", "plan_id"], [])`.
      - Persist document via `MongoIO.get_instance().create_document(config.ENCOUNTER_COLLECTION_NAME, doc)`.
      - Retrieve and enrich each created document with `mentor_name` and `mentee_name`.
    - Return the list of created enriched encounter documents.
- In `src/routes/encounter_routes.py`:
  - Add route on existing blueprint:
    ```python
    @bp.route("/schedule", methods=["POST"])
    @handle_route_exceptions
    def schedule_encounters():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        encounters = EncounterService.schedule_encounters(data, token, breadcrumb)
        logger.info(
            f"schedule_encounters Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(encounters), 201
    ```
- In `test/services/test_encounter_service.py`:
  - Test successful scheduling of multiple encounters (`count=3`) for mentor and admin.
  - Verify appointment dates advance by `recurrence_days`.
  - Verify each encounter is created with `status: "scheduled"`.
  - Verify agenda is auto-filled when `plan_id` is supplied.
  - Verify `mentor_name` and `mentee_name` are present on returned encounter documents.
  - Test `HTTPForbidden` when non-mentor/non-admin or non-owning mentor attempts to schedule.
  - Test `HTTPBadRequest` when required fields are missing.
- In `test/routes/test_encounter_routes.py`:
  - Add test for `POST /api/encounter/schedule` returning 201 with list of created encounters.
  - Add test for 403 / 400 error conditions.

### Craftsmanship Expectations

- Inbound write RBAC, parameter parsing, schedule math, and document creation belong in `EncounterService`.
- Routes remain strictly HTTP request/response handlers with `@handle_route_exceptions`.
- All MongoDB operations route through `MongoIO`.
- Auto-filled agenda from `PlanService` reuses existing `_build_agenda_from_plan`.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_encounter_service.py` — verify scheduling algorithm, appointment windows, status, and RBAC
  - `test/routes/test_encounter_routes.py` — verify POST /api/encounter/schedule returns 201
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml`

## Outputs

- `src/services/encounter_service.py`
- `src/routes/encounter_routes.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

The agent must not update files outside this list.

## Execution Notes
