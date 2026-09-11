# F350 – Update OpenAPI specification for Encounter mutations

**Status:** Shipped  
**Type:** Feature  
**Depends On:** none  
**Description:** Update `docs/openapi.yaml` to specify the external HTTP contract for Encounter mutations outlined in issue #28. Align the `Encounter` component schema with the MongoDB schema (`status` enum `[active, archived, complete, scheduled]`, `appointment` object with `from`/`to`, remove deprecated `date`, add `mentor_name` and `mentee_name` string lookups). Add `ScheduleEncounterInput` schema and `POST /api/encounter/schedule`. Add `POST /api/encounter/{EncounterId}/start` and `POST /api/encounter/{EncounterId}/finish`. Restrict `PATCH /api/encounter/{EncounterId}` description and `EncounterUpdate` schema to allowed fields (`agenda`, `transcript`, `summary`, `tldr`) and document that PATCH is allowed only when status is `active`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Encounter; OpenAPI documents contract with SPAs
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Specification Source of Truth; Grounded in Database Validation Schema
- `tasks/_PLANNING.md` — OpenAPI changes precede implementation
- `README.md`
- `docs/openapi.yaml` — current OpenAPI 3.0 specification
- MongoDB Encounter schema (fetch from running MongoDB Configurator):
  ```bash
  curl -s -X GET "http://localhost:8383/api/configurations/json_schema/Encounter.yaml/latest/" -H "accept: application/json"
  ```

## Goals

- Align `Encounter` component schema in `docs/openapi.yaml`:
  - Update `status` enum to `["active", "archived", "complete", "scheduled"]`.
  - Add `appointment` object schema:
    ```yaml
    appointment:
      type: object
      description: The scheduled appointment window for this encounter
      additionalProperties: false
      properties:
        from:
          type: string
          format: date-time
          description: When the scheduled appointment starts
        to:
          type: string
          format: date-time
          description: When the scheduled appointment ends
    ```
  - Remove deprecated `date` field (reflecting MongoDB `Encounter.yaml`).
  - Add `mentor_name` (type: string, description: Display name of the mentor looked up from Profile) and `mentee_name` (type: string, description: Display name of the mentee looked up from Profile).
- Add `ScheduleEncounterInput` component schema:
  - Required properties: `mentor_id`, `mentee_id`, `plan_id`, `start_date`, `day_of_week`, `time_of_day`, `recurrence_days`, `count`.
  - `plan_id`: string pattern matching ObjectId (`^[0-9a-fA-F]{24}$`).
  - `start_date`: format `date` or `date-time`.
  - `day_of_week`: integer 0–6 (Sunday=0 through Saturday=6) or day name string.
  - `time_of_day`: string pattern matching time format (e.g. `^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$`).
  - `recurrence_days`: integer minimum 1 (default 7).
  - `count`: integer minimum 1 (number of encounters to schedule).
- Add `POST /api/encounter/schedule` endpoint:
  - Tags: `Encounter`
  - Summary: Schedule recurring encounters between a mentor and mentee
  - Request body: `$ref: '#/components/schemas/ScheduleEncounterInput'`
  - Responses:
    - `201`: Successfully created scheduled encounters (array of `Encounter`)
    - `400`: BadRequest
    - `401`: Unauthorized
    - `403`: Forbidden
    - `500`: InternalError
- Add `POST /api/encounter/{EncounterId}/start` endpoint:
  - Tags: `Encounter`
  - Summary: Start an encounter
  - Description: Verifies customer subscription balance, transitions encounter status to `active`, logs an encounter started event, and decrements the customer subscription balance.
  - Path parameter: `EncounterId`
  - Responses:
    - `200`: Successfully started encounter (`Encounter`)
    - `400`: BadRequest (e.g. encounter not in scheduled status)
    - `401`: Unauthorized
    - `403`: Forbidden (e.g. caller is not owning mentor/admin, or insufficient customer subscription balance)
    - `404`: NotFound
    - `500`: InternalError
- Add `POST /api/encounter/{EncounterId}/finish` endpoint:
  - Tags: `Encounter`
  - Summary: Finish an encounter
  - Description: Transitions encounter status from `active` to `complete`.
  - Path parameter: `EncounterId`
  - Responses:
    - `200`: Successfully finished encounter (`Encounter`)
    - `400`: BadRequest (e.g. encounter not in active status)
    - `401`: Unauthorized
    - `403`: Forbidden
    - `404`: NotFound
    - `500`: InternalError
- Restrict `PATCH /api/encounter/{EncounterId}` and `EncounterUpdate` component schema:
  - Update description to state: only permitted when current status is `active`.
  - Restrict properties in `EncounterUpdate` schema strictly to:
    - `agenda` (array of objects with `checked: boolean` and optional `step: string`)
    - `transcript` (string, maxLength 4096)
    - `summary` (string, maxLength 4096)
    - `tldr` (string, pattern `^[^\t\n]{0,255}$`)
  - Disallow updating `mentor_id`, `mentee_id`, `plan_id`, `status`, `appointment`, `date`, `_id`, `created`, `saved`.

### Craftsmanship Expectations

- Maintain consistency with existing OpenAPI 3.0 conventions in `docs/openapi.yaml` (tags, response refs, error schemas).
- Ground definitions in the MongoDB schema definitions from the live configurator.
- Keep response schemas aligned with the actual enriched output structures.

## Testing Expectations

Run all commands from this API repository root:

- **Validation & Unit Tests**:
  - `pipenv run test` — existing test suite continues to pass.
  - `pipenv run lint` — lint checks pass.
  - `pipenv run build` — package compilation passes.
  - Validate that `docs/openapi.yaml` is syntactically valid YAML and conforms to OpenAPI 3.0:
    ```bash
    pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"
    ```
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - Verify OpenAPI spec is served successfully:
    ```bash
    curl -s http://localhost:8391/docs/openapi.yaml | grep "/api/encounter/schedule"
    ```

## Outputs

- `docs/openapi.yaml`

The agent must not update files outside this list.

## Execution Notes

1. Updated `docs/openapi.yaml`:
   - `Encounter` component schema aligned: removed `date`, added `appointment` object schema (`from`/`to`), added `mentor_name` and `mentee_name` string fields, and updated `status` enum to `["active", "archived", "complete", "scheduled"]`.
   - Added `ScheduleEncounterInput` component schema with required fields: `mentor_id`, `mentee_id`, `plan_id`, `start_date`, `day_of_week`, `time_of_day`, `recurrence_days`, `count`.
   - Restricted `EncounterUpdate` component schema to `agenda`, `transcript`, `summary`, and `tldr` only with `additionalProperties: false`.
   - Added `POST /api/encounter/schedule` endpoint with 201 response returning array of `Encounter`.
   - Added `POST /api/encounter/{EncounterId}/start` endpoint with 200 response returning updated `Encounter`.
   - Added `POST /api/encounter/{EncounterId}/finish` endpoint with 200 response returning updated `Encounter`.
   - Updated `PATCH /api/encounter/{EncounterId}` description to note active status requirement and restricted field updates.
2. Verified YAML syntax with python3 (`yaml.safe_load`).
3. Ran `pipenv run test` (159 passed) and `pipenv run lint` (clean).
