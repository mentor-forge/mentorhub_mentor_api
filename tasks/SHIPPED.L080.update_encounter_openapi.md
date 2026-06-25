# L080 – Update Encounter OpenAPI spec (RBAC, required create fields, agenda, remove list)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Update `docs/openapi.yaml` **first** (design specification, ahead of code) to reflect the new Encounter contract: `POST /api/encounter` requires `mentor_id`, `mentee_id`, and `plan_id` and auto-fills the `agenda` from the referenced Plan's `checklist`; `GET /api/encounter/{EncounterId}` is readable by any `mentor` or `admin`; `PATCH /api/encounter/{EncounterId}` is restricted to `admin` or the owning mentor (the caller's Profile `_id` equals the encounter's `mentor_id`); and the `GET /api/encounter` list endpoint is **removed** (nothing consumes it — the app lists encounters via Get Profile). This is the contract-only task; service/route/test changes land in L090–L110.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- `src/routes/encounter_routes.py` — current routes (POST, GET list, GET by id, PATCH) for the shapes being documented.
- `src/services/encounter_service.py` — current service behavior (note `get_encounters_for_mentee` / `get_recent_encounter` are used by the Profile composite and are **not** part of the removed list endpoint).
- `../mentorhub_mongodb_api/configurator/dictionaries/Encounter.0.1.0.yaml` — Encounter storage shape, including `agenda` (array of `{checked: boolean, step: sentence}`).
- `../mentorhub_mongodb_api/configurator/dictionaries/Plan.0.1.0.yaml` — Plan storage shape; the `checklist` (array of sentences) is the source for the auto-filled `agenda`.

## Goals

- **POST `/api/encounter`**: `EncounterInput` lists `mentor_id`, `mentee_id`, and `plan_id` under `required`; the operation description states these three are required and that the server auto-fills `agenda` from the referenced Plan's `checklist` (the client must not send `agenda`). Keep the `400` (validation) and `404` (referenced Plan not found) responses documented in addition to `401`/`403`/`500`.
- **`agenda` schema**: the `Encounter` response schema includes an `agenda` array of objects with `checked` (boolean) and `step` (string, sentence) to match the Encounter dictionary. `agenda` is **not** part of `EncounterInput` (server-populated). Decide and document whether `EncounterUpdate` may modify `agenda` (allow `agenda` in `EncounterUpdate` so checklist items can be checked off).
- **GET `/api/encounter/{EncounterId}`**: description states any `mentor` or `admin` may read any encounter; retains `401`/`404`/`500` (add `403` only if the contract narrows read access — here read is open to any mentor/admin, so no `403` needed for unrelated mentors).
- **PATCH `/api/encounter/{EncounterId}`**: description states the caller must be `admin` **or** the mentor who owns the encounter (the caller's Profile `_id` equals the encounter's `mentor_id`); retains the `403` and `404` responses.
- **Remove GET list**: delete the `get` operation under the `/api/encounter` path item (the infinite-scroll list). Leave the `post` operation under `/api/encounter` intact. Remove any now-orphaned list-only response wiring that is not shared with other endpoints.
- OpenAPI document still parses and has no dangling `$ref`s.

## Testing Expectations

Run all commands from the **API repository root**.

- **Lint / build**
  - `pipenv run lint` — `black --check` (no Python changes expected here, but keep the repo clean).
  - `pipenv run build` — compile sources.
- **OpenAPI validation**
  - Parse `docs/openapi.yaml` and confirm: no dangling `$ref`s; the `/api/encounter` path has a `post` but no `get`; `EncounterInput.required` includes `mentor_id`, `mentee_id`, `plan_id`; the `Encounter` schema exposes `agenda`.
- **Packaging verification (when infra available)**
  - `pipenv run container`, `pipenv run api`, then `curl -s http://localhost:8391/docs/openapi.yaml | head` to confirm the packaged API serves the updated document.

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — required create fields + agenda-autofill description on POST; `agenda` added to `Encounter` (and `EncounterUpdate`); RBAC wording on GET-by-id and PATCH; removal of the `GET /api/encounter` list operation.

The agent must not update files outside this list.

## Execution Notes

### Summary of changes (`docs/openapi.yaml`)

- **POST `/api/encounter`**: rewrote the operation `description` to state that
  `mentor_id`, `mentee_id`, and `plan_id` are required and that the server
  auto-fills `agenda` from the referenced Plan's `checklist` (client must not
  send `agenda`). Added `400` (`BadRequest`) and `404` (`NotFound`, referenced
  Plan not found) responses alongside the existing `401`/`403`/`500`. The role
  wording was updated from "staff or admin" to "mentor or admin".
- **Removed GET list**: deleted the `get` operation (infinite-scroll list,
  `operationId: getEncounters`) under the `/api/encounter` path item. The `post`
  operation is retained. No response components were orphaned by the removal —
  the deleted operation only used shared `$ref`s (`BadRequest`, `Unauthorized`,
  `InternalError`) that remain in use elsewhere, so none were removed. (The
  pre-existing unused `InfiniteScrollResponse` schema was never wired to this
  operation and was left untouched.)
- **`Encounter` response schema**: added an `agenda` array property; each item
  is an object with `checked` (boolean) and `step` (string, sentence pattern
  `^[^\t\n]{1,255}$`), matching the Encounter dictionary.
- **`EncounterUpdate`**: added the same `agenda` array so checklist items can be
  checked off via PATCH.
- **`EncounterInput`**: added `required: [mentor_id, mentee_id, plan_id]` and
  clarified the description; `agenda` is intentionally **not** present (server-
  populated).
- **GET `/api/encounter/{EncounterId}`**: description now states read is open —
  any `mentor` or `admin` may read any encounter (no ownership check, no `403`).
- **PATCH `/api/encounter/{EncounterId}`**: description now states the caller
  must be `admin` **or** the owning mentor (caller's Profile `_id` equals the
  encounter's `mentor_id`); `403` and `404` responses retained.

### Test / validation results

- **OpenAPI validation** (temporary PyYAML + `$ref`-walking script, since
  removed): PASS — document parses as valid YAML; no dangling `$ref`s;
  `/api/encounter` has a `post` and no `get`; `EncounterInput.required` includes
  `mentor_id`/`mentee_id`/`plan_id`; `Encounter` and `EncounterUpdate` expose
  `agenda`; `EncounterInput` does not; POST exposes `400`/`401`/`403`/`404`/`500`.
- **`pipenv run build`**: PASS (sources compile).
- **`pipenv run lint`** (`black --check`): FAIL, but **pre-existing and
  unrelated** — black flags 29 Python files, none of which were touched by this
  task (`git status` shows only `docs/openapi.yaml` modified). OpenAPI is YAML
  and is not affected by black, so this introduces no regression.

### Deferrals / follow-ups

- **Packaging verification** (`pipenv run container` / `pipenv run api` / curl
  `/docs/openapi.yaml`) was **deferred** — container infra was not exercised in
  this contract-only task. Optional per the task.
- The pre-existing repo-wide `black` formatting failures are out of scope for
  this task (Outputs are limited to `docs/openapi.yaml`); they should be
  addressed separately.
