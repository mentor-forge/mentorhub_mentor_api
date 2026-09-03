# F348 – Pin api-utils 1.0.1

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Implement the dependency half of [F-RA15 / issue #29](https://github.com/mentor-forge/mentorhub_mentor_api/issues/29): pin `api-utils` from `1.0.0` to `1.0.1` so Mentor API consumes the Token contract that exposes `display_name` instead of `name`. Application replacements land in F349.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — pin exact semver for `api-utils`; install via `pipenv run install` after `mh`
- `tasks/_PLANNING.md` — CodeArtifact install is `pipenv run install` (not bare `pipenv install`); lock via `scripts/pipenv-lock.sh` when hashes must refresh
- `tasks/_ORCHESTRATE.md`
- `README.md` — currently documents `api-utils==1.0.0`
- `Pipfile` / `Pipfile.lock` — currently pin `api-utils==1.0.0` on the `codeartifact` index
- `../mentorhub_api_utils/README.md` — `create_flask_token()` returns `display_name` (not `name`); JWT wire claim remains OIDC `name`

**Issue**: [F-RA15:bump_utils](https://github.com/mentor-forge/mentorhub_mentor_api/issues/29) — bump `api_utils` to **1.0.1**.

**External prerequisite**: `api-utils==1.0.1` must resolve from the CodeArtifact index. If `scripts/pipenv-lock.sh` / `pipenv run install` cannot resolve 1.0.1, set **Status** to `Blocked` and stop. Run `mh` once per shell if CodeArtifact credentials are missing. Do **not** fall back to a path install of the sibling checkout.

**Installed package is source of truth** for 1.0.1. After install, inspect the CodeArtifact copy (the sibling `mentorhub_api_utils` working tree may still differ locally):

```bash
pipenv run python -c "import inspect; from api_utils.flask_utils import token as t; print(inspect.getsource(t.Token.to_dict)); print(inspect.getsource(t.Token._map_claims)); print(inspect.getsource(t.create_flask_token))"
```

Confirm `create_flask_token()` / `Token.to_dict()` expose **`display_name`** and no longer include Flask-token `"name"` as the display field. JWT claim `name` may still be mapped into that `display_name` value.

This task is **dependency pin only**. Do not rewrite routes, services, tests, OpenAPI, or README here (README pin text is F349). Do **not** paper over a pin failure with a local Token shim.

**Orchestrator:** A `pipenv run test` failure whose traceback is only Flask-token `name` vs `display_name` is **expected** and is **not** a Task Failure Case. Record it in Execution Notes, mark this task Shipped after the pin/install/inspect goals succeed, and continue to F349. Halt only if 1.0.1 will not resolve, install fails, or tests fail for a different reason.

## Goals

- `Pipfile` pins `api-utils==1.0.1` with `index = "codeartifact"` (keep the existing comment that the PyPI package named `api-utils` is unrelated).
- `Pipfile.lock` is regenerated against CodeArtifact (`scripts/pipenv-lock.sh`) and consumed by `pipenv run install`.
- `pip show api-utils` (inside the Pipenv) reports **1.0.1**.
- Import check after install:
  ```python
  from api_utils.flask_utils.token import Token, create_flask_token

  assert callable(create_flask_token)
  assert hasattr(Token, "to_dict")
  ```
  Plus the inspect check above: `to_dict` keys include `display_name` (not Flask-token `name` as the display field).
- No `src/`, `test/`, `docs/`, or `README.md` edits in this task.

### Craftsmanship Expectations

- Treat the installed shared library as the single source of truth for token claim shape. Do not vendor or copy `Token` / `create_flask_token` into this repo.
- Do not bump to `1.1.0` or an unreleased sibling version; the issue is **1.0.1**.
- MongoDB I/O stays on `MongoIO`; this task does not touch `src/services/`.
- Do not introduce a local compatibility alias that accepts both `name` and `display_name`.

## Testing Expectations

Run all commands from this API repository root.

- **Install**
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `sh scripts/pipenv-lock.sh`
  - `pipenv run install`
  - Inspect installed `Token.to_dict` / `_map_claims` as above
- **Unit tests**
  - `pipenv run test` — existing suite against 1.0.1 **before** F349. Token-field-only failures: document, do not revert the pin, proceed (see Orchestrator note).
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - Defer `pipenv run container` / `pipenv run api` / `pipenv run e2e` to F349 so the image and e2e JWTs are verified after `display_name` replacements. Optionally `pipenv run container` here if unit tests are already green and you want an early image check; it is not required to mark this task Shipped.

## Outputs

- `Pipfile` — pin `api-utils==1.0.1`
- `Pipfile.lock` — refresh via `scripts/pipenv-lock.sh` and `pipenv run install`

The agent must not update files outside this list.

## Execution Notes

### Plan

1. Pin-only: change `Pipfile` `api-utils` from `==1.0.0` to `==1.0.1` (`index = "codeartifact"`; keep the existing PyPI-unrelated comment). Do not edit `src/`, `test/`, `docs/`, or `README.md`.
2. Refresh `Pipfile.lock` with `scripts/pipenv-lock.sh` (CodeArtifact token + `pipenv lock --pypi-mirror`). If 1.0.1 will not resolve, set Status to Blocked and stop — no sibling path install, no local Token shim.
3. Install with `pipenv run install` (not bare `pipenv install`). Confirm `pipenv run pip show api-utils` reports 1.0.1.
4. Inspect the **installed** package (`Token.to_dict`, `Token._map_claims`, `create_flask_token`) and confirm Flask-token `display_name` (JWT wire claim `name` may still map into that value).
5. Run `pipenv run test`, `pipenv run lint`, `pipenv run build`. Token-field-only test failures are expected and not a Task Failure Case; document them and proceed. Halt if tests fail for a different reason.
6. Defer `container` / `api` / `e2e` to F349. After pin/install/inspect succeed, mark Shipped.

### Implementation

- `Pipfile`: `api-utils = {version = "==1.0.1", index = "codeartifact"}` (PyPI-unrelated comment unchanged).
- `Pipfile.lock`: regenerated via `scripts/pipenv-lock.sh`; `api-utils` `version` is `==1.0.1` with new hashes (`98b6d9ad…`, `ce68399b…`).
- No `src/`, `test/`, `docs/`, or `README.md` edits (README pin text remains F349).

### Version confirmation

- `pipenv run pip show api-utils` → **1.0.1** (installed from CodeArtifact; replaced 1.0.0).
- Import check: `from api_utils.flask_utils.token import Token, create_flask_token` — `create_flask_token` is callable; `Token.to_dict` exists.

### Token contract audit (installed 1.0.1)

- `Token.to_dict()` keys: `user_id`, **`display_name`**, `roles`, `profile_id`, `customer_id`, `mentor_id`, `remote_ip`. No Flask-token `"name"` display field.
- `display_name` value: `self.claims.get("name") or self.claims.get("display_name") or ""` — JWT OIDC `name` still maps into `display_name`.
- `Token._map_claims()` maps `sub` → `user_id`, normalizes `roles` to a list, requires `profile_id`, defaults `customer_id` / `mentor_id`. Does not add a Flask-token `name` key.
- `create_flask_token()` returns `Token().to_dict()`.

### Test results

- `sh scripts/pipenv-lock.sh` — success (1.0.1 resolved from CodeArtifact).
- `pipenv run install` — success (`Successfully installed api-utils-1.0.1`).
- `pipenv run test` — **156 passed**, 43 deselected (e2e). No token-field `name` vs `display_name` failures; suite was already green against 1.0.1 without F349 rewrites.
- `pipenv run lint` — pass (`50 files would be left unchanged`).
- `pipenv run build` — pass (exit 0).
- Packaging (`container` / `api` / `e2e`) deferred to F349 per task.

### Blockers

None. 1.0.1 resolved and installed. In-scope gates passed.
