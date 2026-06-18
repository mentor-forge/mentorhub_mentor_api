# R010 – Complete Profile RBAC via shared Config role constants

**Status**: Pending  
**Task Type**: Feature  
**Run Mode**: Sequential  <!-- options: Sequential | Run as needed -->

## Goal

Finish the Profile role-based access control (RBAC) feature so that:
- `mentor_api` consumes shared role constants from `api_utils.Config` instead of declaring role strings locally.
- The Profile endpoints authorize **both** the `mentor` and `admin` roles.
- The change is fully releasable: `api_utils` is published with the new constants and `mentor_api` pins that published version (no editable-install dependency).

## Context / Input files

These files must be treated as **inputs** and read before implementation:

- `mentorhub_api_utils/api_utils/config/config.py` – where the shared role constants (`ADMIN_ROLE`, `MENTOR_ROLE`, `MENTEE_ROLE`, `CUSTOMER_ROLE`, `COORDINATOR_ROLE`, `ALL_ROLES`) will live.
- `mentorhub_api_utils/pyproject.toml` – package version to bump.
- `mentorhub_mentor_api/Pipfile` – `api-utils` version pin (currently `==0.2.1`).
- `mentorhub_mentor_api/src/services/profile_service.py` – `_check_permission` (mentor OR admin).
- `mentorhub_mentor_api/test/services/test_profile_service.py` – RBAC unit tests.
- `mentorhub_mentor_api/docs/openapi.yaml` – Profile endpoint docs (role wording + `403` responses).

The agent may also consult:

- `mentorhub/DeveloperEdition/standards/api_standards.md` – API + documentation standards.
- CodeArtifact publishing/auth flow (`mh` CLI) used by sibling services.

## Requirements

- **api_utils**
  - Add the role constants to `Config` so they are importable as `Config.MENTOR_ROLE` / `Config.ADMIN_ROLE`, etc.
  - Bump the package version in `pyproject.toml`.
  - Build and publish the package to CodeArtifact.
- **mentor_api**
  - Replace any locally declared role strings with the shared `Config` constants.
  - Authorize both `mentor` and `admin` for all Profile operations.
  - Bump the `api-utils` pin in `Pipfile` to the newly published version and reinstall (`pipenv run install`) so the build no longer relies on an editable install.
  - Ensure `openapi.yaml` documents the role requirement ("`mentor` or `admin`") and the `403` response on both Profile endpoints.

## Testing expectations

- **Unit tests**
  - `pipenv run test` in `mentorhub_mentor_api` and `mentorhub_api_utils`.
  - Cover: mentor allowed, admin allowed, other roles denied (`403`).
- **End-to-end (e2e) tests**
  - `pipenv run e2e` in `mentorhub_mentor_api` (against a running API at `localhost:8391`).
  - Confirm an authorized role can read the Profile endpoints.

## Packaging / build checks

Before marking this task as completed:

- `api_utils`: build/publish succeeds and the new version is resolvable from CodeArtifact.
- `mentor_api`: `pipenv run install` resolves the new `api-utils` pin (no editable install), and `pipenv run container` (or `make container`) builds successfully.
- No new linter/type-checking errors (`pipenv run lint`).

## Dependencies / Ordering

- Must run **after**: the `api_utils` role constants are merged and published (the `mentor_api` Pipfile pin cannot be bumped until the new version exists in CodeArtifact).
- Target branches: `feature/role-constants` (api_utils), `dashboard-refactor` (mentor_api).

## Open questions for review

1. **api_utils versioning/publish**: when the role-constants change merges, *what `api_utils` version gets published to CodeArtifact, and how is that number decided* (auto-bump by the pipeline, git tag, or manual)? This determines the exact `mentor_api` Pipfile pin and is the main external dependency for this task.
2. Should adopting the shared role constants in the other domain APIs (coordinator, customer, mentee) be folded in here, or tracked as a separate follow-up?

## Change control checklist

- [ ] Reviewed all **Context / Input files**.
- [ ] Designed and documented the solution approach in this file.
- [ ] Implemented code changes (role constants + RBAC + OpenAPI wording).
- [ ] Bumped `api_utils` version and published to CodeArtifact.
- [ ] Bumped `mentor_api` `Pipfile` pin and reinstalled (no editable install).
- [ ] Added/updated **unit tests**.
- [ ] Added/updated **e2e tests**.
- [ ] Ran unit tests and e2e tests; all passing.
- [ ] Ran packaging/build steps (`pipenv run container` / `make container`); build successful.
- [ ] Created a scoped commit referencing this task ID.

## Implementation notes (to be updated by the agent)

**Summary of changes**
- _TBD_

**Testing results**
- Unit tests: _command(s) run, high-level outcome_
- E2E tests: _command(s) run, high-level outcome_
- Packaging/build: _command(s) run, high-level outcome_

**Follow-up tasks**
- Adopt the shared role constants in the other domain APIs (coordinator, customer, mentee) to remove their local role strings.
