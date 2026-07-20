# L210 – Harvest alignment: prefer api_utils.services for harvested read paths

**Status**: Pending  
**Type**: Feature  
**Depends On**: L200_scoped_lists_pagination  
**Description**: Sweep the service layer so that **read paths** for domains already harvested into `api_utils.services` (Note, Event, Journey, Path, Resource) prefer the shared implementation, while **mentor-only domains** (Mentee, Encounter, Plan, Profile) are **retained locally for now**. This consolidates the per-domain migrations from L160–L200 into a consistent policy and removes any remaining duplicated read logic for harvested domains. The local retention of mentor-only domains is an **interim state**, not the target architecture: it stands only until those domains are harvested upstream (see `ISSUE.mentorhub_api_utils.harvest_mentor_services.md`), after which the Mentor API adopts the shared services and deletes `src/services/` (see `ISSUE.mentorhub_mentor_api.adopt_harvested_services.md`).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `src/services/resource_service.py`
- `src/services/event_service.py`
- `src/services/journey_service.py`
- `src/services/path_service.py`
- `src/services/mentee_service.py`
- `src/services/encounter_service.py`
- `src/services/plan_service.py`
- `src/services/profile_service.py`
- `src/routes/` (all route modules for the affected domains)
- `docs/openapi.yaml`
- `test/services/` and `test/e2e/` (affected domains)

**Shared service surface (api_utils 0.5.0)**

- Inspect `api_utils.services` to confirm exactly which domains and read methods are harvested (expected: Note, Event, Journey, Path, Resource read paths). Only delegate reads that the shared package actually provides; record the confirmed surface in **Execution Notes**.

**Policy to apply**

- **Harvested read paths** (Note, Event, Journey, Path, Resource): prefer `api_utils.services.*` — import directly or keep a thin local wrapper that delegates. Remove duplicated local read logic.
- **Mentor-only domains** (Mentee, Encounter, Plan, Profile): keep local **for now**. These carry mentor-specific RBAC/composition (owner-patch, dashboard aggregation, per-mentee scoping) that has not yet been harvested, so the shared service cannot replace them **yet**. This is a temporary retention pending upstream harvesting (`ISSUE.mentorhub_api_utils.harvest_mentor_services.md`); it is not the final architecture.
- Domain-specific write/CRUD and mentor-only composition stay local even for harvested domains (as established in L160–L180) **until harvested** — the target end state is that all domains resolve from `api_utils.services` and this repo carries no local service layer (`ISSUE.mentorhub_mentor_api.adopt_harvested_services.md`).

**Current-state notes**

- "Note" corresponds to the mentee-notes document owned by `MenteeService`; confirm whether its **read** is among the harvested paths before delegating. If the harvested "Note" service does not match the mentor-notes semantics, keep it local and record why.
- `JourneyService` currently exposes only aggregation (`get_journey_progress`) consumed by the dashboard; delegate only the parts that have a harvested equivalent, keep aggregation local if it does not.

**Follow-on (cross-repo) artifacts**

- `tasks/ISSUE.mentorhub_api_utils.harvest_mentor_services.md` — upstream harvest of the mentor-only domains (blocker for adoption).
- `tasks/ISSUE.mentorhub_mentor_api.adopt_harvested_services.md` — this repo's adoption of the harvested services and removal of `src/services/`, blocked on that release. These describe the end state that supersedes the interim local retention below.

**MongoIO rule**

- All retained local reads/writes must route MongoDB I/O through `MongoIO` (no direct PyMongo). Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`.

## Goals

- Read paths for harvested domains (Note/Event/Journey/Path/Resource, per the confirmed shared surface) are served by `api_utils.services.*` with no duplicated local read logic remaining.
- Mentor-only domains (Mentee/Encounter/Plan/Profile) remain local with unchanged RBAC and composition semantics.
- The policy is applied consistently and any divergence (e.g. Note kept local) is documented in **Execution Notes**.
- Full unit and E2E suites pass.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`
  - `pipenv run dev`
  - `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/resource_service.py` — confirm read delegation; remove any residual local read logic
- `src/services/event_service.py` — confirm read delegation; remove any residual local read logic
- `src/services/journey_service.py` — delegate harvested read parts; keep local aggregation if unharvested
- `src/services/path_service.py` — confirm read delegation; remove any residual local read logic
- `src/services/mentee_service.py` — delegate Note read only if harvested semantics match; else document local retention
- `docs/openapi.yaml` — reflect any read-path changes from this consolidation
- `test/services/*` and `test/e2e/*` for affected domains — update to match delegated read paths

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
