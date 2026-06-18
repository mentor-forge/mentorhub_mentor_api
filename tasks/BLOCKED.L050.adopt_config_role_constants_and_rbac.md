# L050 – Adopt shared Config role constants and allow admin + mentor

**Status**: Blocked  
**Type**: Feature  
**Depends On**: L040  
**Description**: Replace locally declared role strings with the shared role constants on `api_utils.Config`, and update the RBAC permission checks to authorize **both** the `admin` and `mentor` roles. Bump the `api-utils` version pin in the `Pipfile` to the published version that exposes the role constants.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- `Pipfile` — `api-utils` version pin
- `src/services/*_service.py` — `_check_permission` implementations and any local role strings
- `api_utils.Config` — shared role constants (`ADMIN_ROLE`, `MENTOR_ROLE`, etc.)

**External prerequisite**: `api_utils` must publish a version that exposes the role constants on `Config` (e.g. `Config.MENTOR_ROLE`, `Config.ADMIN_ROLE`). Confirm the published version is resolvable from CodeArtifact before starting. If it is not yet available, set **Status** to `Blocked` and stop. (Run `mh` first for CodeArtifact auth.)

## Goals

- The `Pipfile` `api-utils` pin is bumped to the published version that includes the `Config` role constants; `pipenv run install` resolves it (no editable install).
- All RBAC checks reference the shared constants (`Config.MENTOR_ROLE` / `Config.ADMIN_ROLE`) instead of hard-coded role strings.
- Permission checks authorize **both** `admin` and `mentor` where mentor access is currently allowed (including the Profile and Mentee endpoints).
- `docs/openapi.yaml` endpoint descriptions state the "`mentor` or `admin`" requirement and keep the `403` responses.

## Testing Expectations

Run all commands from the **API repository root**.

- **Install**
  - `pipenv run install` resolves the new `api-utils` pin.
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - Update RBAC unit tests: `mentor` allowed, `admin` allowed, other roles denied (`403`).
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8391`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API (no editable install).

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump the `api-utils` version pin
- `src/services/profile_service.py` — use `Config` role constants; allow `admin` + `mentor`
- `src/services/mentee_service.py` — use `Config` role constants; allow `admin` + `mentor`
- Any other `src/services/*_service.py` that declare local role strings — switch to `Config` constants
- `docs/openapi.yaml` — role wording ("`mentor` or `admin`") and `403` responses on the affected endpoints
- `test/services/test_profile_service.py`, `test/services/test_mentee_service.py` — RBAC allow/deny assertions for `mentor` and `admin`

The agent must not update files outside this list.

## Execution Notes

**BLOCKED on external prerequisite (api_utils role constants not published).**

Pre-flight verification (2026-06-18):
- Imported `api_utils` resolves to the editable working tree `../mentorhub_api_utils` (`api_utils.__file__` → `.../mentorhub_api_utils/api_utils/__init__.py`), currently on branch `main`.
- `Config` exposes **no** role constants: `hasattr(Config, 'MENTOR_ROLE') == False`, `hasattr(Config, 'ADMIN_ROLE') == False`, `[a for a in dir(Config) if 'ROLE' in a] == []`.
- `Pipfile` still pins `api-utils == 0.2.1`; no newer version with role constants is resolvable.

Because the shared role constants do not exist in the `api_utils` this repo imports, this task cannot adopt them or bump the pin. Per the task's external-prerequisite rule, Status is set to **Blocked** and execution stopped.

**To unblock:** publish an `api_utils` version that defines the role constants (e.g. `Config.MENTOR_ROLE`, `Config.ADMIN_ROLE`, and ideally `MENTEE_COLLECTION_NAME`), then bump the `Pipfile` pin and re-run this task.

**Interim option (not done here, requires approval):** the "allow admin + mentor" half could be implemented now using local role strings in each service's `_check_permission`, deferring the shared-constant adoption to when api_utils ships. This deviates from the task as written, so it was left for the developer to decide.
