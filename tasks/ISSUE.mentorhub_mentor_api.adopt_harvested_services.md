# Adopt harvested `api_utils.services`; retire local `src/services/`

> **Cross-repo issue artifact.** Paste-ready description for follow-on planning
> in **`mentorhub_mentor_api`**. Not part of the current `PENDING.LNNN`
> orchestration chain and must not be executed from this folder.
> **Blocked on**: release of `ISSUE.mentorhub_api_utils.harvest_mentor_services.md`
> (the `api_utils` version that harvests Plan/Encounter/Mentee/Profile and extends
> Resource/Event/Path/Journey to full-domain services). Sequence serially after
> that release is published to CodeArtifact.

## Summary

Once `api_utils.services` carries the full Resource, Event, Path, Journey, Plan,
Encounter, Mentee, and Profile domains (see the harvest issue), the Mentor API
should consume them directly and delete its local service layer. This removes the
duplicated wrappers left in place temporarily by L160–L210 and makes
`api_utils.services` the single source of truth.

## Scope

- **Dependency bump**: pin `api-utils` to the harvested release (next minor
  beyond `0.5.0`, e.g. `0.6.0`) in `Pipfile`/`Pipfile.lock`; install via
  `pipenv run install` (CodeArtifact auth; run `mh` first if needed).
- **Direct adoption**: import and use `api_utils.services.*` directly in the
  route layer (`src/routes/`) for all eight domains, replacing calls into local
  `src/services/*`.
- **Remove local wrappers**: delete the thin local delegating wrappers and any
  retained local CRUD/composition (Resource/Event/Path CRUD, Plan, Encounter,
  Mentee, Profile) that now live upstream.
- **Remove duplicated tests**: delete `test/services/*` unit tests that merely
  re-test behavior now covered by upstream `api_utils` tests; keep only
  Mentor-API-specific route/E2E tests.
- **Delete `src/services/` entirely** after parity verification — no local
  service module should remain.

## Parity verification (before deletion)

- Behavior matches per-domain against the pre-adoption contract: RBAC
  (mentor/admin; Encounter owner-or-admin; Path update mentor/admin), validation
  and `steps`⇄`checklist` mapping, offset/size header pagination + `sort_by`/`order`,
  ObjectId handling, and composites (Profile detail/dashboard, Encounter
  agenda-from-Plan).
- Full suites green: `pipenv run test`, `pipenv run lint`, `pipenv run build`,
  and dev + containerized `pipenv run e2e`.
- OpenAPI (`docs/openapi.yaml`) still matches the served contract (no behavior
  drift introduced by adoption).

## Acceptance

- Routes call `api_utils.services.*` directly; `src/services/` is deleted.
- Confirmation (e.g. `rg 'src\.services'` / `rg 'from src.services'`) that **no
  `src.services` imports remain** anywhere in `src/` or `test/`.
- Confirmation that **no direct MongoDB access remains** in this repo — no
  PyMongo calls and no local `MongoIO` usage in application code (all storage is
  reached through `api_utils.services`).
- Unit + E2E suites pass against the containerized API.
