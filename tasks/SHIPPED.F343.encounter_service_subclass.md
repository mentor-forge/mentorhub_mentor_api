# F343 – EncounterService subclass (harvest-back writes)

**Status:** Complete  
**Type:** Feature  
**Depends On:** `F342_plan_service_subclass`  
**Description:** Subclass shared `EncounterService`. Inherit GET helpers (`get_encounter`, `get_encounters_for_mentee`, `get_recent_encounter`). Keep owner-or-admin write RBAC and agenda-from-plan create locally — R079 strips those writes from api-utils. Read RBAC stays on the shared parent (outbound). Do not switch routes and do not pin 1.0.0.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentor **controls** Encounter
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
- `../mentorhub_api_utils/README.md` — inbound writes on the subclass; do not 403 on GET
- `../mentorhub_api_utils/api_utils/services/encounter_service.py` — 1.0.0 parent: `get_encounter`, `get_encounters_for_mentee`, `get_recent_encounter`, `_normalize_mentee_id`; outbound mentor/mentee identity + `status != archived`
- `src/services/encounter_service.py` — standalone class that currently 403s non-mentors on **read**; local create (agenda from Plan via `PlanService.get_plan`) and owner-or-admin update
- `src/services/plan_service.py` — local subclass from F342 (`create_encounter` must keep calling **local** `PlanService`)
- `src/services/profile_service.py` — `get_profile_by_token` used for owner check (lazy import already)
- `test/services/test_encounter_service.py`

**MongoDB I/O:** Writes go through `MongoIO`. Encode `mentor_id` / `mentee_id` / `plan_id` with `encode_document` immediately before `create_document`. Do not call PyMongo via `mongo.get_collection(...)`.

**Do not** edit route modules or `Pipfile`. Convert `@staticmethod` to `@classmethod`. Delete local copies of GET helpers that the parent already implements (`get_encounter`, `get_encounters_for_mentee`, `get_recent_encounter`, `_normalize_mentee_id`). Dashboard callers keep using `EncounterService.get_recent_encounter` via inheritance.

Do **not** 403 on GET for “not a mentor”. Do **not** override parent `_check_permission` in a way that gates `read`. Put inbound write checks on `_check_permission_write` as in the harvest-back.

Create requires `ROLE_MENTOR` (admin is root). Update: owning mentor (`encounter.mentor_id` equals caller Profile `_id`) or admin.

Harvest-back writes:

```python
@classmethod
def _validate_update_data(cls, data):
    restricted_fields = ["_id", "created", "saved"]
    for field in restricted_fields:
        if field in data:
            raise HTTPForbidden(f"Cannot update {field} field")

@classmethod
def _build_agenda_from_plan(cls, plan):
    steps = plan.get("steps")
    if steps is None:
        steps = plan.get("checklist")
    if not steps:
        return []
    return [{"step": step, "checked": False} for step in steps]

@classmethod
def _check_permission_write(cls, token, operation, breadcrumb, encounter=None):
    from api_utils.services.profile_service import ProfileService
    config = Config.get_instance()
    roles = token.get("roles", []) or []
    if config.ROLE_ADMIN in roles:
        return
    if config.ROLE_MENTOR not in roles:
        raise HTTPForbidden("Mentor or admin role required to access encounter data")
    if encounter is not None:
        profile = ProfileService.get_profile_by_token(token, breadcrumb)
        caller_profile_id = profile.get("_id") if profile else None
        if caller_profile_id is None or str(caller_profile_id) != str(
            encounter.get("mentor_id")
        ):
            raise HTTPForbidden(
                "Only the owning mentor or an admin may update this encounter"
            )

@classmethod
def create_encounter(cls, data, token, breadcrumb):
    try:
        cls._check_permission_write(token, "create", breadcrumb)
        plan = PlanService.get_plan(data["plan_id"], token, breadcrumb)
        data["agenda"] = cls._build_agenda_from_plan(plan)
        if "_id" in data:
            del data["_id"]
        encode_document(data, ["mentor_id", "mentee_id", "plan_id"], [])
        data["created"] = breadcrumb
        data["saved"] = breadcrumb
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        encounter_id = mongo.create_document(config.ENCOUNTER_COLLECTION_NAME, data)
        return encounter_id
    except (HTTPForbidden, HTTPNotFound):
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to create encounter: {e}")

@classmethod
def update_encounter(cls, encounter_id, data, token, breadcrumb):
    try:
        cls._check_permission_write(token, "update", breadcrumb)
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        encounter = mongo.get_document(config.ENCOUNTER_COLLECTION_NAME, encounter_id)
        if encounter is None:
            raise HTTPNotFound(f"Encounter {encounter_id} not found")
        cls._check_permission_write(token, "update", breadcrumb, encounter=encounter)
        cls._validate_update_data(data)
        restricted_fields = ["_id", "created", "saved"]
        set_data = {k: v for k, v in data.items() if k not in restricted_fields}
        set_data["saved"] = breadcrumb
        updated = mongo.update_document(
            config.ENCOUNTER_COLLECTION_NAME,
            document_id=encounter_id,
            set_data=set_data,
        )
        if updated is None:
            raise HTTPNotFound(f"Encounter {encounter_id} not found")
        return updated
    except (HTTPForbidden, HTTPNotFound):
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to update encounter {encounter_id}")
```

Prefer resolving the caller Profile through **local** `src.services.profile_service.ProfileService.get_profile_by_token` (lazy import) rather than `api_utils.services.profile_service`, so F346’s subclass is what ownership checks use. The harvest-back snippet above is the algorithm; swap that import.

`create_encounter` must import `PlanService` from `src.services.plan_service`.

## Goals

- `src/services/encounter_service.py` subclasses `api_utils.services.EncounterService`.
- Local: `_build_agenda_from_plan`, `_check_permission_write`, `create_encounter`, `update_encounter`.
- Inherited: GET helpers including `get_recent_encounter` (dashboard).
- Create requires mentor/admin; update is owner-or-admin; GET is not 403-gated in this subclass.
- Unit tests mock MongoIO / `PlanService.get_plan` / `ProfileService.get_profile_by_token`; must pass on `api-utils==0.5.1`.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_encounter_service.py` — create allowed for mentor (agenda from plan steps/checklist); `HTTPForbidden` without mentor/admin; update allowed for owning mentor and admin, forbidden for another mentor; missing encounter → 404; inherited GET helpers exist; no 403-on-GET assertion against the subclass for a non-mentor **read** (parent outbound covers visibility)
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served

## Outputs

- `src/services/encounter_service.py`
- `test/services/test_encounter_service.py`

The agent must not update files outside this list.

## Execution Notes

1. Subclassed `EncounterService` from `api_utils.services.EncounterService` (with fallback for `api-utils==0.5.1`).
2. Implemented `_build_agenda_from_plan`, `_check_permission_write` (mentor/admin on create; owner mentor or admin on update via local `ProfileService.get_profile_by_token`), `create_encounter`, and `update_encounter`.
3. Preserved inherited GET helpers including `get_recent_encounter`, `get_encounter`, and `get_encounters_for_mentee`.
4. Updated unit tests in `test/services/test_encounter_service.py` to verify write RBAC and inherited methods.
5. Formatted, linted, built, and verified all unit tests pass.

