# L100 – Encounter RBAC: open read for mentor/admin, owner-or-admin PATCH

**Status**: Pending  
**Type**: Feature  
**Depends On**: L080  
**Description**: Implement RBAC for the Encounter read and update endpoints. `GET /api/encounter/{EncounterId}` is readable by any caller with the `mentor` or `admin` role (any mentor can read any encounter). `PATCH /api/encounter/{EncounterId}` is allowed only for `admin`, or for the mentor who **owns** the encounter — i.e. the caller's Profile `_id` equals the encounter's `mentor_id`. Replace the placeholder `_check_permission` in `EncounterService` with these real checks.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README_API.md`
- `README.md`
- `docs/openapi.yaml` (after L080)

Additional inputs:

- `src/services/encounter_service.py` — `_check_permission`, `get_encounter`, `update_encounter`.
- `src/services/profile_service.py` — the ownership pattern: the caller's Profile is resolved from the JWT identity (`token["user_id"]` matches `Profile.name`); that Profile's `_id` is the mentor id used across the domain. Reuse the shared role constants `Config.ROLE_MENTOR` / `Config.ROLE_ADMIN` (see L050 notes) and the same identity-resolution approach.
- `src/routes/encounter_routes.py` — GET-by-id and PATCH routes (no signature change expected; RBAC lives in the service).
- `test/services/test_encounter_service.py`, `test/routes/test_encounter_routes.py`, `test/e2e/test_encounter.py`.

## Goals

- **Read (`get_encounter`)**: authorize any caller whose roles include `Config.ROLE_MENTOR` or `Config.ROLE_ADMIN`; deny others with `HTTPForbidden` (`403`). A mentor may read **any** encounter (no ownership check on read).
- **Update (`update_encounter`)**: authorize `admin` unconditionally; otherwise require the `mentor` role **and** ownership — resolve the caller's Profile (`Profile.name == token["user_id"]`) and confirm its `_id` equals the target encounter's `mentor_id`. Non-owner mentors and other roles are denied with `HTTPForbidden` (`403`). A missing encounter still yields `HTTPNotFound` (`404`).
- Implement ownership without `EncounterService` reaching across collections inappropriately: resolve the caller Profile via `ProfileService` (or an equivalent shared helper) consistent with existing conventions, and load the encounter to read its `mentor_id`. Compare ids as strings to avoid `ObjectId` vs `str` mismatches.
- Keep `_validate_update_data` restrictions (`_id`, `created`, `saved`) and the existing `saved`-breadcrumb update behavior.
- Ensure `HTTPForbidden` and `HTTPNotFound` are re-raised (not wrapped to `500`).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests** — `pipenv run test`. Add/extend `test/services/test_encounter_service.py`:
  - `get_encounter`: allowed for `mentor`, allowed for `admin`, denied (`403`) for a role with neither.
  - `update_encounter`: allowed for `admin`; allowed for the owning mentor (caller Profile `_id == mentor_id`); denied (`403`) for a non-owning mentor; denied (`403`) for other roles; `404` when the encounter does not exist.
  - Route tests (`test/routes/test_encounter_routes.py`): GET-by-id and PATCH return the appropriate `200` / `403` / `404` for representative tokens.
- **Lint / build** — `pipenv run lint`, `pipenv run build`.
- **Dev / E2E (when infra available)** — `pipenv run db`, `pipenv run dev`, `pipenv run e2e`; extend `test/e2e/test_encounter.py` with owner-allowed and non-owner-denied PATCH cases (`@pytest.mark.e2e`).

## Outputs

Paths are relative to the **API repository root**.

- `src/services/encounter_service.py` — real `_check_permission` / ownership logic for read and update.
- `test/services/test_encounter_service.py` — RBAC allow/deny tests for read and update.
- `test/routes/test_encounter_routes.py` — GET-by-id and PATCH RBAC route assertions.
- `test/e2e/test_encounter.py` — (optional) owner/non-owner PATCH e2e (`@pytest.mark.e2e`).

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
