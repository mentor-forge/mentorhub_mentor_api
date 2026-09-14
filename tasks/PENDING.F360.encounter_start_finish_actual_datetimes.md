# F360 – Populate started and completed date-time in start and finish encounter mutations

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F359_encounter_openapi_schema`  
**Description:** Update `start_encounter` and `finish_encounter` in `EncounterService` to populate the `actual` datetime fields. Starting an encounter populates `actual.from` with the current UTC datetime (or breadcrumb `at_time`). Finishing an encounter populates `actual.to` with the current UTC datetime while preserving `actual.from`. Update unit tests in `test/services/test_encounter_service.py` to verify that `actual` fields are persisted and returned in enriched documents.

## Path Anchoring

All paths are relative to **this API repository root** (the directory that contains `Pipfile`).

- Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
- In-repo: `src/services/encounter_service.py`, `test/services/test_encounter_service.py`, `tasks/`

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Stateless business logic and service mutation lifecycles
- `tasks/_PLANNING.md` — MongoIO only
- `tasks/_ORCHESTRATE.md`
- `README.md`
- `docs/openapi.yaml` — `POST /api/encounter/{EncounterId}/start` and `finish` endpoint contracts
- `src/services/encounter_service.py` — `start_encounter` and `finish_encounter` methods
- `test/services/test_encounter_service.py` — unit tests for encounter lifecycle mutations
- Running schema server endpoint: `http://localhost:8383/api/configurations/json_schema/Encounter.yaml/latest/`

## Goals

- In `src/services/encounter_service.py`:
  - Update `start_encounter(cls, encounter_id, token, breadcrumb)`:
    - Derive start timestamp: `started_at = breadcrumb.get("at_time") or datetime.now(timezone.utc)`.
    - Retrieve or initialize `actual = dict(encounter.get("actual") or {})`.
    - Set `actual["from"] = started_at`.
    - Persist `actual` in `mongo.update_document`:
      ```python
      updated = mongo.update_document(
          config.ENCOUNTER_COLLECTION_NAME,
          document_id=encounter_id,
          set_data={"status": "active", "actual": actual, "saved": breadcrumb},
      )
      ```
    - Return the enriched encounter document (which now contains `actual.from`).
  - Update `finish_encounter(cls, encounter_id, token, breadcrumb)`:
    - Derive completed timestamp: `completed_at = breadcrumb.get("at_time") or datetime.now(timezone.utc)`.
    - Retrieve or initialize `actual = dict(encounter.get("actual") or {})`.
    - Set `actual["to"] = completed_at`.
    - Persist `actual` in `mongo.update_document`:
      ```python
      updated = mongo.update_document(
          config.ENCOUNTER_COLLECTION_NAME,
          document_id=encounter_id,
          set_data={"status": "complete", "actual": actual, "saved": breadcrumb},
      )
      ```
    - Return the enriched encounter document (which now contains `actual.from` and `actual.to`).
- In `test/services/test_encounter_service.py`:
  - In `test_start_encounter_success`:
    - Verify `actual` is passed to `mongo.update_document` in `set_data` with `"from"` populated.
    - Verify returned encounter contains `actual` with `"from"` matching the start timestamp.
  - In `test_finish_encounter_success`:
    - Seed existing encounter mock with `actual: {"from": datetime(2026, 7, 19, 2, 2, tzinfo=timezone.utc)}`.
    - Verify `actual` is passed to `mongo.update_document` in `set_data` with `"to"` populated and `"from"` preserved.
    - Verify returned encounter contains `actual` with both `"from"` and `"to"`.
  - In `test_update_encounter_prevent_restricted_fields`:
    - Add `"actual"` and `"no_show"` to the list of restricted fields tested against `update_encounter` to verify they raise `HTTPForbidden`.

### Craftsmanship Expectations

- Do not overwrite or lose `actual.from` when setting `actual.to` during `finish_encounter`.
- Keep timestamp generation consistent: use `breadcrumb.get("at_time")` or `datetime.now(timezone.utc)`.
- Enforce PATCH boundary guardrails: `ALLOWED_UPDATE_FIELDS` in `EncounterService` must remain strictly limited to `{"agenda", "transcript", "summary", "tldr"}`. Attempting to update `actual` (or `no_show`) via `PATCH /api/encounter/<encounter_id>` must be rejected with `403 Forbidden`.
- All database modifications must route through `MongoIO.update_document`.
- Enriched documents must contain `mentor_name`, `mentee_name`, and the updated `actual` dictionary.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests & Linting**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `pipenv run pytest test/services/test_encounter_service.py` — verify start and finish logic, subscription decrement, event logging, status transitions, and `actual` timestamp population
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml`

## Outputs

- `src/services/encounter_service.py`
- `test/services/test_encounter_service.py`

The agent must not update files outside this list.

## Execution Notes

<!-- Reserved for task execution agent to record plan, commands run, test results, and follow-ups. -->
