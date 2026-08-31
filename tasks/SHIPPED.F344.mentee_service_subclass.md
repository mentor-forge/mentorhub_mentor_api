# F344 – MenteeService subclass (restore create-if-missing GET)

**Status:** Complete  
**Type:** Feature  
**Depends On:** `F343_encounter_service_subclass`  
**Description:** Subclass shared `MenteeService`. Shared GET is read-only (returns 404 if missing or hidden). Mentor BFF restores create-if-missing on GET and keeps `update_mentee`. Inbound write RBAC is `ROLE_MENTOR` (admin is root). Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Mentee
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; inbound writes on the subclass
- `../mentorhub_api_utils/api_utils/services/mentee_service.py` — 1.0.0 parent: read-only `get_mentee` with outbound scope (own-profile or assigned-mentor); returns 404 when not found; no write methods
- `src/services/mentee_service.py` — standalone class; `get_mentee` does create-if-missing and gates on `ROLE_MENTOR` / `ROLE_ADMIN`; `update_mentee` updates fields with restricted-field guards
- `test/services/test_mentee_service.py`

**MongoDB I/O:** Use `MongoIO` (`get_documents`, `get_document`, `create_document`, `update_document`). Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`.

Preferred wrap (inherit outbound GET; create only on 404):

```python
@classmethod
def get_mentee(cls, profile_id, token, breadcrumb):
    try:
        return super().get_mentee(profile_id, token, breadcrumb)
    except HTTPNotFound:
        cls._check_permission(token, "create")
@classmethod
def _validate_update_data(cls, data):
    for field in RESTRICTED_FIELDS:
        if field in data:
            raise HTTPForbidden(f"Cannot update {field} field")

@classmethod
def _default_document(cls, profile_object_id, breadcrumb):
    return {
        "profile_id": profile_object_id,
        "status": "active",
        "description": "",
        "focus": "",
        "homework": "",
        "notes": "",
        "created": breadcrumb,
        "saved": breadcrumb,
    }

@classmethod
def get_mentee(cls, profile_id, token, breadcrumb):
    try:
        cls._check_permission(token, "read")
        profile_object_id = cls._to_object_id(profile_id, "profile_id")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        collection_name = cls._collection_name(config)
        existing = mongo.get_documents(
            collection_name, match={"profile_id": profile_object_id}
        )
        if existing:
            return existing[0]
        document = cls._default_document(profile_object_id, breadcrumb)
        mentee_id = mongo.create_document(collection_name, document)
        return mongo.get_document(collection_name, mentee_id)
    except (HTTPBadRequest, HTTPForbidden):
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to retrieve mentee for profile {profile_id}")

@classmethod
def update_mentee(cls, mentee_id, data, token, breadcrumb):
    try:
        cls._check_permission(token, "update")
        cls._validate_update_data(data)
        mentee_object_id = cls._to_object_id(mentee_id, "mentee_id")
        set_data = {k: v for k, v in data.items() if k not in RESTRICTED_FIELDS}
        set_data["saved"] = breadcrumb
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        collection_name = cls._collection_name(config)
        updated = mongo.update_document(
            collection_name,
            match={"_id": mentee_object_id},
            set_data=set_data,
        )
        if updated is None:
            raise HTTPNotFound(f"Mentee {mentee_id} not found")
        return updated
    except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to update mentee {mentee_id}")
```

If using the full harvest-back `get_mentee` (not the wrap), **drop** the `_check_permission(token, "read")` gate so GET is not 403-for-non-mentor; still call `_check_permission(token, "create")` on the create-if-missing path. Prefer the wrap so parent outbound visibility stays in one place. Mock `super().get_mentee` in unit tests so they pass against installed `api-utils==0.5.1`.

## Goals

- `src/services/mentee_service.py` subclasses `api_utils.services.MenteeService`.
- GET create-if-missing restored for mentor/admin; existing visible documents return without a write.
- `update_mentee` stays local with restricted-field protection.
- No 403-on-GET for missing mentor role; create/update still require `ROLE_MENTOR` (admin root).
- Unit tests mock MongoIO / `super().get_mentee`; must pass on `api-utils==0.5.1`.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_mentee_service.py` — existing document returned (no create); 404 from `super()` then create-if-missing for mentor; create-if-missing `HTTPForbidden` without mentor/admin; admin may create/update; `update_mentee` restricted fields and 404; remove tests that expected 403 on GET for a non-mentor **read** of an existing document
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served

## Outputs

- `src/services/mentee_service.py`
- `test/services/test_mentee_service.py`

The agent must not update files outside this list.

## Execution Notes

1. Subclassed `MenteeService` from `api_utils.services.MenteeService` (with fallback for `api-utils==0.5.1`).
2. Implemented `get_mentee` wrapping `super().get_mentee` and creating default document on 404 for mentor/admin.
3. Preserved `update_mentee` with restricted field guards and `_check_permission` requiring `ROLE_MENTOR` / `ROLE_ADMIN` on writes.
4. Updated unit tests in `test/services/test_mentee_service.py` verifying get existing, create-if-missing, update, and RBAC error branches.
5. Formatted, linted, built, and verified all unit tests pass.
