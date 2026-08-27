# F341 – ResourceService and PathService subclasses (inherit GETs)

**Status:** Complete  
**Type:** Feature  
**Depends On:** `F340_openapi_1_0_0_list_gets`  
**Description:** Convert Resource and Path from composition (`SharedXService.get_*` inside a standalone class) to inheritance. Keep local `create_*` / `update_*`. Inherit list/by-id GETs. Inbound write RBAC is `ROLE_MENTOR` (admin is root). Do not switch routes and do not pin 1.0.0 — existing routes still call the local class until F347.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Resource and Path
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer; one collection per service
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; outbound GET RBAC stays on the shared class; inbound write checks on the subclass
- `../mentorhub_api_utils/api_utils/services/resource_service.py` — 1.0.0 parent: `get_resources` / `get_resource` / `get_resources_by_ids`; read `_check_permission` is a no-op; outbound `status != archived`
- `../mentorhub_api_utils/api_utils/services/path_service.py` — 1.0.0 `get_path` is the **raw** Path (no mentee resource-summary enrich); `get_paths`
- `../mentorhub_api_utils/api_utils/services/rbac.py` — `is_admin`
- `src/services/resource_service.py` — standalone class; `get_resources` delegates to `SharedResourceService`; local `get_resource` / `create_resource` / `update_resource`; already re-exports `RESOURCE_LIST_FILTERS` / `RESOURCE_LIST_ORDER`
- `src/services/path_service.py` — same composition for `get_paths`; local `get_path` / `create_path` / `update_path`; update already requires mentor/admin; create is authenticated-only today
- `test/services/test_resource_service.py`
- `test/services/test_path_service.py`

**MongoDB I/O:** Use `MongoIO` (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`) or inherited shared methods. Encode string ids with `encode_document` immediately before MongoIO. Do not call PyMongo via `mongo.get_collection(...)`. Do not stringify ObjectIds for output.

**Do not** edit route modules or `Pipfile` in this task. Convert `@staticmethod` to `@classmethod` in every method you touch.

Replace composition:

```python
from api_utils.services import ResourceService as SharedResourceService

class ResourceService:
    def get_resources(...):
        return SharedResourceService.get_resources(...)
```

with:

```python
from api_utils.services import ResourceService as SharedResourceService

class ResourceService(SharedResourceService):
    # inherit get_resources / get_resource / get_resources_by_ids
    @classmethod
    def create_resource(cls, data, token, breadcrumb):
        ...
    @classmethod
    def update_resource(cls, resource_id, data, token, breadcrumb):
        ...
```

Same pattern for `PathService`. **Do not** re-add mentee resource-summary enrich on `get_path`.

**`super()` on 0.5.1:** the installed parent already has list GETs. Delete the local `get_resources` / `get_resource` / `get_paths` / `get_path` wrappers so MRO supplies them. Unit-test inherited GETs by asserting they exist on the subclass; mock `super().get_resource` / `super().get_path` only if a test must not hit the installed parent.

**Inbound RBAC (writes only):** override `_check_permission` so `create` and `update` require `Config.ROLE_MENTOR`. Admin (`ROLE_ADMIN` / `is_admin(token)`) is root. For `read`, call `super()._check_permission(...)` (no-op) — do **not** 403 on GET for “not a mentor”; outbound filters hide rows.

Keep re-exporting `RESOURCE_LIST_FILTERS` / `RESOURCE_LIST_ORDER` and `PATH_LIST_FILTERS` / `PATH_LIST_ORDER` from the local modules so routes keep importing them until F347.

## Goals

- `src/services/resource_service.py` subclasses `api_utils.services.ResourceService`. Local methods: `create_resource`, `update_resource`, write `_check_permission`. Inherited: `get_resources`, `get_resource`, `get_resources_by_ids`.
- `src/services/path_service.py` subclasses `api_utils.services.PathService`. Local methods: `create_path`, `update_path`, write `_check_permission`. Inherited: `get_paths`, raw `get_path`. Create now requires mentor (not authenticated-only).
- Path by-id stays a raw Path document.
- Unit tests mock MongoIO for writes; they do not require a live database and must pass while the process still pins `api-utils==0.5.1`.
- Existing routes still import `src.services.resource_service` / `src.services.path_service`.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_resource_service.py` — `create_resource` / `update_resource` allowed for mentor and admin; `HTTPForbidden` without mentor/admin; restricted `_id`/`created`/`saved` on update; inherited list/by-id methods exist on the subclass
  - `test/services/test_path_service.py` — same write RBAC for create **and** update; inherited `get_paths` / `get_path` exist; no resource-summary enrich on `get_path`
- **Packaging verification** (no HTTP change)
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served

## Outputs

- `src/services/resource_service.py`
- `src/services/path_service.py`
- `test/services/test_resource_service.py`
- `test/services/test_path_service.py`

The agent must not update files outside this list.

## Execution Notes

1. Subclassed `ResourceService` from `api_utils.services.ResourceService`, inheriting `get_resources`, `get_resource`, and `get_resources_by_ids` while preserving local `create_resource`, `update_resource`, and `_check_permission` for mentor/admin write RBAC.
2. Subclassed `PathService` from `api_utils.services.PathService`, inheriting `get_paths` and raw `get_path` while preserving local `create_path`, `update_path`, and `_check_permission` requiring mentor/admin for both create and update.
3. Updated unit tests in `test/services/test_resource_service.py` and `test/services/test_path_service.py` to verify write RBAC (mentor/admin allowed, non-mentor forbidden), restricted field guards, and inherited GET methods existence.
4. Formatted, linted, compiled, and passed full unit test suite.

