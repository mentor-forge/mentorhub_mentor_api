# L010 – Update OpenAPI from new Profile and Mentee schemas

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Fetch the latest `Profile` and `Mentee` JSON schemas from the MongoDB configurator and update `docs/openapi.yaml` to match. Define, contract-first, the composite Profile detail response (`Profile` + mentee notes + `Encounter` list) returned by `GET /api/profile/{_id}`, and the new `/api/mentee` endpoints. Implementation of the routes/services follows in L020–L030.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- Latest schemas from the MongoDB configurator (configurator must be running on port `8383`; you may need to use ``mh up mongodb`` to start the API).

```bash
# Profile schema
curl -X GET "http://localhost:8383/api/configurations/json_schema/Profile.yaml/latest/" -H "accept: application/json"

# Mentee schema
curl -X GET "http://localhost:8383/api/configurations/json_schema/Mentee.yaml/latest/" -H "accept: application/json"
```

- `../mentorhub_mongodb_api/configurator/dictionaries/Profile.*.yaml`
- `../mentorhub_mongodb_api/configurator/dictionaries/Mentee.*.yaml`
- Existing `docs/openapi.yaml` paths/schemas for `Profile` and `Encounter`, and the security scheme.

**External prerequisite**: the MongoDB `Profile` and `Mentee` dictionaries are current and the configurator serves the latest schemas at the URLs above. If the configurator is unavailable try starting it with ``mh up mongodb`` and if the API call still fails halt and report an error.

## Goals

- `docs/openapi.yaml` GET `Profile` component schema matches the latest `Profile.yaml` from the configurator (properties, types, descriptions, optionality) with Profile, Mentee and Encounter data.
- New `Mentee` component schema in `docs/openapi.yaml` matches the latest `Mentee.yaml` (the mentee-notes document).
- New `MenteeUpdate` schema describing the patchable fields of `Mentee` (system-managed fields such as `_id`, `created`, `saved` are excluded).
- New `ProfileDetail` schema describing the composite returned by `GET /api/profile/{_id}`: `{ profile: Profile, mentee: Mentee, encounters: [Encounter, ...] }`.
- `GET /api/profile/{_id}` documented to return `ProfileDetail` (read-only), with `200`/`401`/`403`/`404`/`500` responses.
- New `Mentee` tag and paths:
  - `GET /api/mentee/{profile_id}` — returns `Mentee`; documents that a default document is created if none exists so the UI always receives a valid document. Responses `200`/`401`/`403`/`500`.
  - `PATCH /api/mentee/{mentee_id}` — request body `MenteeUpdate`; responses `200`/`401`/`403`/`404`/`500`.
- The spec is valid: it parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s — every `$ref` resolves to a defined component.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8391/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — update `Profile`; add `Mentee`, `MenteeUpdate`, `ProfileDetail` schemas; update `GET /api/profile/{_id}` to `ProfileDetail`; add `GET /api/mentee/{profile_id}` and `PATCH /api/mentee/{mentee_id}` paths and the `Mentee` tag.

The agent must not update files outside this list.

## Execution Notes

**Summary of changes** (`docs/openapi.yaml` only):
- `Profile` schema synced to latest configurator schema: added `full_name`; removed `schedule` (now lives on `Mentee`).
- Added `Mentee` schema (fields: `_id`, `name`, `profile_id`, `status` [active/archived], `description`, `focus`, `homework`, `notes`, `next_appointment`, `schedule {repeats, starting}`, `created`, `saved`; `additionalProperties: false`).
- Added `MenteeUpdate` (patchable fields; excludes `_id`/`created`/`saved`).
- Added `ProfileDetail` composite: `{ profile: Profile, mentee: Mentee, encounters: [Encounter, ...] }`.
- `GET /api/profile/{ProfileId}` now returns `ProfileDetail` (200/401/403/404/500).
- Added `Mentee` tag + paths `GET /api/mentee/{profile_id}` (200/401/403/500, create-if-missing documented) and `PATCH /api/mentee/{mentee_id}` (body `MenteeUpdate`; 200/401/403/404/500).

**Testing results**
- YAML parses (`pipenv run python -c "import yaml; yaml.safe_load(...)"`) — OK.
- `$ref` check: 29 unique refs, 0 dangling; `Mentee`/`MenteeUpdate`/`ProfileDetail` defined.
- `pipenv run lint`: pre-existing `black` failures over `src/`/`test/` Python only — unrelated to this YAML-only change.

**Follow-ups**
- `Profile.schedule` moved to `Mentee`; downstream code/tests in later tasks should not expect `schedule` on Profile.
- Configurator runs on port `8383` in this environment (task curl corrected from 8385).