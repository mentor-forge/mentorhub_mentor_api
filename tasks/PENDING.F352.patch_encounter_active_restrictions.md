# F352 – Enforce PATCH encounter active status and allowed fields restrictions

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F351_encounter_name_enrichment`  
**Description:** Restrict `PATCH /api/encounter/<id>` guardrails: allow updates only when encounter `status == "active"` and restrict updatable fields strictly to `agenda` (`agenda.checked`), `transcript`, `summary`, and `tldr`. Reject updates with `HTTPForbidden` if status is not `active` (e.g. `scheduled`, `complete`, `archived`) or if any disallowed field is present in the update payload.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC and guardrails strictly enforced at Service layer
- `tasks/_PLANNING.md`
- `README.md`
- `docs/openapi.yaml` — `EncounterUpdate` restricted schema
- `src/services/encounter_service.py` — `update_encounter` and `_validate_update_data`
- `src/routes/encounter_routes.py` — PATCH route handler
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

## Goals

- In `src/services/encounter_service.py`:
  - Update `_validate_update_data(cls, data)`:
    - Define `ALLOWED_UPDATE_FIELDS = {"agenda", "transcript", "summary", "tldr"}`.
    - Check every key in `data`: if any key is not in `ALLOWED_UPDATE_FIELDS`, raise `HTTPForbidden(f"Cannot update field '{field}'")`.
    - If `agenda` is present in `data`:
      - Validate that `agenda` is a list of dicts.
      - Validate that each item contains at least `"checked"` as a boolean (and optionally `"step"` as a string).
  - In `update_encounter(cls, encounter_id, data, token, breadcrumb)`:
    - Enforce active status requirement:
      - After fetching `encounter` from database, inspect `encounter.get("status")`.
      - If `encounter.get("status") != "active"`:
        raise `HTTPForbidden(f"Cannot update encounter: status must be 'active', got '{encounter.get('status')}'")`.
    - Keep existing owner-or-admin check (`_check_permission_write`).
    - Only update allowed fields, stamp `saved: breadcrumb`, and save via `MongoIO.update_document`.
    - Return the enriched updated encounter document.
- In `test/services/test_encounter_service.py`:
  - Test PATCH succeeds when status is `"active"` and updating allowed fields (`agenda`, `transcript`, `summary`, `tldr`).
  - Test PATCH raises `HTTPForbidden` when encounter status is `"scheduled"`.
  - Test PATCH raises `HTTPForbidden` when encounter status is `"complete"`.
  - Test PATCH raises `HTTPForbidden` when encounter status is `"archived"`.
  - Test PATCH raises `HTTPForbidden` when payload includes disallowed fields (e.g. `status`, `mentor_id`, `mentee_id`, `plan_id`, `appointment`, `date`, `name`, `_id`, `created`, `saved`).
  - Test PATCH preserves agenda checklist updates.
- In `test/routes/test_encounter_routes.py`:
  - Update tests to reflect allowed field payloads on PATCH and forbidden error handling.

### Craftsmanship Expectations

- Inbound write RBAC, field whitelist validation, and state machine guardrails belong strictly in `EncounterService` (`src/services/encounter_service.py`).
- Do not alter or validate payloads in the route module (`src/routes/encounter_routes.py`); routes remain thin HTTP pass-through.
- Provide clear error messages when rejecting disallowed fields or non-active statuses.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_encounter_service.py` — verify active status checks, allowed fields validation, and rejection of disallowed fields
  - `test/routes/test_encounter_routes.py` — verify HTTP 200 and 403 responses
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml`

## Outputs

- `src/services/encounter_service.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

The agent must not update files outside this list.

## Execution Notes
