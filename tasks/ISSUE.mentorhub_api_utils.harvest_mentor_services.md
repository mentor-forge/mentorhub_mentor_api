# Harvest Mentor-API services into `api_utils.services`

> **Cross-repo issue artifact.** Paste-ready description for planning in
> **`mentorhub_api_utils`**. Not part of `mentorhub_mentor_api`'s
> `PENDING.LNNN` orchestration chain and must not be executed from this repo.
> Sequencing: this release is the **blocker** for
> `ISSUE.mentorhub_mentor_api.adopt_harvested_services.md`.

## Summary

`api_utils.services` is the canonical home for reusable, model-like API services
shared across Journey APIs. Services are thin wrappers around validated
`MongoIO` storage — comparable to ODM models plus domain behavior. This issue
completes the shared service surface consumed by the Mentor API list migrations
(`mentorhub_mentor_api` L150–L210, which pin `api-utils==0.5.0`) by extending the
already-harvested read services and harvesting the remaining Mentor-API domains.

## Scope

### 1. Extend existing shared services (Resource, Event, Path, Journey)

The 0.5.0 list/read surface (`api_utils.services.ResourceService`,
`EventService`, `PathService`, and the Journey read/aggregation used by the
Mentor dashboard) is consumed for **read paths** only. Extend each so the full
domain — not just list reads — lives upstream:

- **Resource** — add CRUD (`create_resource`, `update_resource`) alongside the
  existing `get_resources` list (offset/size header pagination, `name` filter,
  `sort_by`/`order` per `order_spec`).
- **Event** — add `get_event` (by-id) and `create_event` (with `_id`/`profile_id`
  ObjectId encoding via `ID_PROPERTIES`) alongside `get_events`
  (`type`/`profile_id` filters, `EVENT_LIST_ORDER`).
- **Path** — add CRUD (`create_path`, `get_path`, `update_path` with
  mentor/admin RBAC via `Config.ROLE_MENTOR`/`ROLE_ADMIN`) alongside `get_paths`.
- **Journey** — add the progress aggregation (`get_journey_progress`,
  library/now/next resource counts for the active Journey) if not already
  upstream.

### 2. Harvest remaining Mentor-API domains

Move these services from `mentorhub_mentor_api/src/services/` to
`api_utils.services`, preserving behavior exactly:

- **Plan** — `create_plan`, `get_plans` (name-asc list; add offset/size header
  pagination + optional `name` "contains" filter to match the shared
  convention), `get_plan`, `update_plan`; API `steps` ⇄ storage `checklist`
  mapping and validation; restricted-field guard (`_id`/`created`/`saved`).
- **Encounter** — `create_encounter` (required `mentor_id`/`mentee_id`/`plan_id`,
  ObjectId encoding of those refs, agenda auto-filled from the referenced Plan's
  checklist), `get_encounter`, `update_encounter` (mentor/admin read; **owner-or-admin**
  patch resolving the caller Profile via `ProfileService`), and the per-mentee
  reads `get_encounters_for_mentee` / `get_recent_encounter` (optional offset/size
  scoped to `mentee_id`, `date`-desc order, defaulting to the full list for
  composite callers).
- **Mentee** — `get_mentee` (create-if-missing default document) and
  `update_mentee`; mentor/admin RBAC; `profile_id` ObjectId handling; restricted-field
  guard.
- **Profile** — `get_profile_by_token` (resolve caller Profile by `name` ==
  token `user_id`), `get_profiles` (Mentor Dashboard composite: one card per
  assigned mentee + Journey progress + recent Encounter summary), `get_profile`
  (composite detail: Profile + Mentee notes + Encounter list), and
  `get_profile_properties` (Profile/Journey/Resource/Encounter aggregation).

## Invariants to preserve

- **Validation**: required-field / restricted-field checks and reliance on the
  collection `$jsonSchema` validator; `steps`⇄`checklist` mapping.
- **RBAC**: shared `Config` role constants; Mentee/Profile require mentor/admin;
  Encounter owner-or-admin patch; Path update mentor/admin; unchanged
  `HTTPForbidden`/`HTTPNotFound`/`HTTPBadRequest` semantics.
- **Pagination**: offset/size **request headers**, pagination **response
  headers**, standardized `sort_by`/`order` query params, plain-array bodies (no
  cursor/infinite-scroll envelope).
- **ObjectId handling**: `encode_document`/`ObjectId` coercion for id fields
  (`mentor_id`, `mentee_id`, `plan_id`, `profile_id`), tolerant string/ObjectId
  normalization for scoped matches.
- **Composition**: service-to-service calls (Profile → Mentee/Encounter/Journey;
  Encounter → Plan/Profile) with lazy imports to avoid cycles — no direct
  cross-collection access for composites.
- **MongoIO-only access**: all I/O through `MongoIO` (`get_document`,
  `get_documents`, `create_document`, `update_document`, `upsert_document`); no
  direct PyMongo.

## Deliverables

- Services added/extended under `api_utils/services/` and exported from
  `api_utils.services` (and re-exported from the package root as appropriate).
- Upstream unit/integration tests for every harvested/extended service (RBAC,
  validation, pagination, ObjectId encoding, composition), plus demo-server/E2E
  coverage where relevant.
- README/service docs updated to list the new shared services.
- Version bump in `pyproject.toml` (next minor beyond `0.5.0`, e.g. `0.6.0`) and
  publication to **AWS CodeArtifact** via the standard release flow
  (`pipenv run tag-release` after merge).

## Acceptance

- `api_utils.services` exposes Resource/Event/Path/Journey (full domain) and
  Plan/Encounter/Mentee/Profile with the invariants above intact.
- New version published to CodeArtifact and installable by domain APIs.
- Full upstream test suite green (`pipenv run test`, `pipenv run lint`,
  `pipenv run build`).
