# F342 – PlanService subclass (harvest-back writes)

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F341_resource_path_service_subclasses`  
**Description:** Subclass shared `PlanService` so list/by-id GETs come from api-utils. Keep `create_plan` / `update_plan` locally — R079 strips those from the shared class. Inbound write RBAC is `ROLE_MENTOR` (admin is root). Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Plan
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; inbound writes on the subclass; do not 403 on GET
- `../mentorhub_api_utils/api_utils/services/plan_service.py` — 1.0.0 parent: `get_plans`, `get_plan`, `PLAN_LIST_FILTERS` / `PLAN_LIST_ORDER`; read-only (no create/update)
- `../mentorhub_api_utils/api_utils/services/rbac.py` — `is_admin`
- `src/services/plan_service.py` — standalone local class with its own list query **and** create/update; `_check_permission` is a no-op today; defines local `PLAN_LIST_FILTERS` / `PLAN_LIST_ORDER`
- `test/services/test_plan_service.py`

**MongoDB I/O:** Writes go through `MongoIO.create_document` / `update_document`. Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`. Delete local `get_plans` / `get_plan` so the parent supplies them. Re-export `PLAN_LIST_FILTERS` / `PLAN_LIST_ORDER` from the shared module (same names) so `src/routes/plan_routes.py` keeps compiling until F347.

**Inbound RBAC (writes only):** `_check_permission` for `create` / `update` requires `ROLE_MENTOR`. Admin is root. Do **not** 403 on `read`.

Harvest-back writes (adapt to `classmethod` / `MongoIO.get_instance()` already used in this repo):

```python
@classmethod
def _validate_update_data(cls, data):
    restricted_fields = ["_id", "created", "saved"]
    for field in restricted_fields:
        if field in data:
            raise HTTPForbidden(f"Cannot update {field} field")

@classmethod
def create_plan(cls, data, token, breadcrumb):
    try:
        cls._check_permission(token, "create")
        if "_id" in data:
            del data["_id"]
        data["created"] = breadcrumb
        data["saved"] = breadcrumb
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        plan_id = mongo.create_document(config.PLAN_COLLECTION_NAME, data)
        return plan_id
    except HTTPForbidden:
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to create plan: {e}")

@classmethod
def update_plan(cls, plan_id, data, token, breadcrumb):
    try:
        cls._check_permission(token, "update")
        cls._validate_update_data(data)
        restricted_fields = ["_id", "created", "saved"]
        set_data = {k: v for k, v in data.items() if k not in restricted_fields}
        set_data["saved"] = breadcrumb
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        updated = mongo.update_document(
            config.PLAN_COLLECTION_NAME, document_id=plan_id, set_data=set_data
        )
        if updated is None:
            raise HTTPNotFound(f"Plan {plan_id} not found")
        return updated
    except (HTTPForbidden, HTTPNotFound):
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to update plan {plan_id}")
```

## Goals

- `src/services/plan_service.py` subclasses `api_utils.services.PlanService`.
- Local: `create_plan`, `update_plan`, write `_check_permission`, `_validate_update_data`.
- Inherited: `get_plans`, `get_plan`.
- Filter/order constants are re-exported from the shared module, not duplicated.
- Unit tests mock MongoIO; they must pass while the process still pins `api-utils==0.5.1`.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_plan_service.py` — create/update allowed for mentor and admin; `HTTPForbidden` without mentor/admin; restricted fields on update; 404 when update misses; inherited GET methods exist on the subclass
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served

## Outputs

- `src/services/plan_service.py`
- `test/services/test_plan_service.py`

The agent must not update files outside this list.

## Execution Notes
