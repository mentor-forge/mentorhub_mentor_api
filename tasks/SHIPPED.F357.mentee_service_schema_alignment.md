# F357 – Update MenteeService implementation and unit tests for simplified schema

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F356_mentee_openapi_schema`  
**Description:** Update `MenteeService._default_document` in `src/services/mentee_service.py` to produce schema-compliant default documents containing `summary` and `notes` without legacy fields (`description`, `focus`, `homework`). Update `test/services/test_mentee_service.py` to validate the new document shape and test updates with `summary`.

## Path Anchoring

All paths are relative to **this API repository root** (the directory that contains `Pipfile`).

- Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
- In-repo: `src/services/mentee_service.py`, `test/services/test_mentee_service.py`, `tasks/`

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `tasks/SHIPPED.F356.mentee_openapi_schema.md`
- `docs/openapi.yaml`
- `src/services/mentee_service.py`
- `test/services/test_mentee_service.py`
- Running schema server endpoint: `http://localhost:8383/api/dictionaries/Mentee.0.1.0.yaml/`

### Schema Alignment Details

MongoDB collection validator rejects any documents with unrecognized fields (`additionalProperties: false`).
`_default_document` currently initializes:
```python
doc = {
    "_id": profile_id,
    "status": "active",
    "description": "",
    "focus": "",
    "homework": "",
    "notes": "",
    "created": breadcrumb,
    "saved": breadcrumb,
}
```
Under the updated schema, `description`, `focus`, and `homework` must be replaced with `summary`:
```python
doc = {
    "_id": profile_id,
    "status": "active",
    "summary": "",
    "notes": "",
    "created": breadcrumb,
    "saved": breadcrumb,
}
```

## Goals

- In `src/services/mentee_service.py`:
  - Update `_default_document(cls, profile_id, breadcrumb)`:
    - Initialize `_id`, `status: "active"`, `summary: ""`, `notes: ""`, `created`, `saved`.
    - Remove `description`, `focus`, and `homework`.
  - Update `_validate_update_data(cls, data)`:
    - Retain rejection of `RESTRICTED_FIELDS` (`_id`, `profile_id`, `created`, `saved`).
    - Explicitly reject deprecated/disallowed fields (`description`, `focus`, `homework`, `schedule`, `next_appointment`, `name`) with `HTTPForbidden("Cannot update {field} field")` or restrict updates strictly to allowed properties (`summary`, `notes`, `status`).
- In `test/services/test_mentee_service.py`:
  - Update tests that assert `_default_document` shape (`test_get_mentee_creates_when_missing_for_mentor`, `test_get_mentee_creates_when_missing_for_admin`):
    - Assert `document["summary"] == ""` and `document["notes"] == ""`.
    - Assert `description`, `focus`, and `homework` are not present in the created document.
  - Update `test_update_mentee_prevent_restricted_fields` or add negative tests verifying that attempting to update legacy fields (`description`, `focus`, `homework`, etc.) is rejected with `HTTPForbidden`.
  - Update `test_update_mentee_success` to test updating `summary` and `notes`.

### Craftsmanship Expectations

- Strict conformance to the MongoDB schema validator (`additionalProperties: false`).
- Preserve all existing RBAC logic (admin, mentor-of-profile, self-read).

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests**:
  - `pipenv run test`
- **Lint & Build**:
  - `pipenv run lint`
  - `pipenv run build`

## Outputs

- `src/services/mentee_service.py`
- `test/services/test_mentee_service.py`

The agent must not update files outside this list.

## Execution Notes

- Updated `MenteeService._default_document` to initialize `_id`, `status: "active"`, `summary: ""`, `notes: ""`, `created`, and `saved`, removing legacy fields `description`, `focus`, and `homework`.
- Updated `MenteeService._validate_update_data` to restrict updates strictly to `ALLOWED_UPDATE_FIELDS = {"summary", "notes", "status"}` and reject any legacy/disallowed fields with `HTTPForbidden`.
- Updated `test/services/test_mentee_service.py`:
  - Verified default document assertions for mentor and admin create-if-missing paths.
  - Verified rejection of restricted and legacy fields (`_id`, `profile_id`, `created`, `saved`, `focus`, `homework`, `description`, `schedule`, `next_appointment`, `name`).
  - Verified successful update of `summary` and `notes`.
- All 190 unit tests passed and linting was clean.

