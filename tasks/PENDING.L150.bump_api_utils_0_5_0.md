# L150 – Bump dependency to api-utils==0.5.0

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Bump the pinned `api-utils` dependency from `==0.2.4` to `==0.5.0` (published from `api_utils` release R054) so this API can consume the harvested shared list services (`api_utils.services.*`) and header-based pagination/order helpers used by the follow-on tasks. This task only lands the dependency bump and confirms the app still builds and passes the existing suite; behavioral migration happens in L160–L230.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATION.md`
- `Pipfile`
- `Pipfile.lock`

**Current state**

- `Pipfile` pins `api-utils = {version = "==0.2.4", index = "codeartifact"}`.
- The vendored `0.2.4` does **not** expose `api_utils.services.*`; those shared read services (Resource/Event/Journey/Path/Note plus `order_spec` / `EVENT_LIST_ORDER` / offset-size header helpers) arrive in `0.5.0`. Confirm the exact public surface by inspecting the installed package after the bump (`.venv/.../api_utils/services/`), or the `api_utils` repo at the R054 tag.

**External prerequisite**

- `api-utils==0.5.0` must be **published to CodeArtifact** (release R054 in `../mentorhub_api_utils`) before this task can install. If `0.5.0` is not resolvable from the CodeArtifact index, set **Status** to `Blocked` and stop.

## Goals

- `Pipfile` pins `api-utils = {version = "==0.5.0", index = "codeartifact"}`.
- `Pipfile.lock` is regenerated so `api-utils` resolves to `0.5.0` (via the repo's CodeArtifact auth wrapper).
- `api_utils.services` is importable in the project virtualenv (smoke check, e.g. `pipenv run python -c "import api_utils.services"`).
- Existing unit tests, lint, and build all pass unchanged (no behavioral changes in this task).

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`). Run `mh` once per shell session first if CodeArtifact credentials are not already available.

- **Dependency install** (required — `Pipfile` / `Pipfile.lock` changed)
  - `pipenv run install`
  - Smoke check: `pipenv run python -c "import api_utils, api_utils.services; print(api_utils.__version__ if hasattr(api_utils, '__version__') else 'ok')"`

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`

- **Build**
  - `pipenv run build`

- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify OpenAPI is served: `curl -s http://localhost:8391/docs/openapi.yaml | head`

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump `api-utils` pin to `==0.5.0`
- `Pipfile.lock` — regenerated lock reflecting `api-utils==0.5.0`

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
