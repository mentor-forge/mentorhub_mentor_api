# F344 – MenteeService subclass (create-if-missing + update)

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F343_encounter_service_subclass`  
**Description:** Subclass shared `MenteeService`. Shared `get_mentee` is read-only (404 if missing or hidden). Restore create-if-missing on GET and `update_mentee` on the Mentor subclass (R079 removed those writes). Inbound create-if-missing / update require `ROLE_MENTOR`. Do not 403 on a successful GET. Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md` — inbound writes on the subclass; outbound GET on the parent
- `../mentorhub_api_utils/api_utils/services/mentee_service.py` — 1.0.0 parent: `get_mentee` 404 if missing/hidden; `_to_object_id`, `_collection_name`, `_require_mentee_visible`; read `_check_permission` is a no-op
- `src/services/mentee_service.py` — standalone create-if-missing GET plus `update_mentee`; currently 403s non-mentors on **read**
- `test/services/test_mentee_service.py`

**MongoDB I/O:** Use `MongoIO` or inherited shared methods. Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`.

**Preferred wrap** (inherit outbound GET; create only on 404):

```python
@classmethod
def get_mentee(cls, profile_id, token, breadcrumb):
    try:
        return super().get_mentee(profile_id, token, breadcrumb)
    except HTTPNotFound:
        cls._check_permission(token, "create")
        # _default_document + create_document + get_document (harvest-back body)
```

Override `_check_permission` so `create` / `update` require `ROLE_MENTOR`. Admin is root. For `read`, call `super()._check_permission` — do **not** 403 on GET for “not a mentor”. A non-mentor whose outbound scope can see an existing document still receives it; create-if-missing is mentor-only.

Harvest-back helpers and `update_mentee` (classmethod form). If you wrap GET instead of pasting the full `get_mentee`, still keep `_default_document` / `update_mentee` / `_validate_update_data`:

```python
RESTRICTED_FIELDS = ["_id", "created", "saved"]

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
