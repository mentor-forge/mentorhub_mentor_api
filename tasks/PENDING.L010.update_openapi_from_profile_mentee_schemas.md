# L010 – Update OpenAPI from new Profile and Mentee schemas

**Status**: Pending  
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

- Latest schemas from the MongoDB configurator (configurator must be running, port `8385`):

```bash
# Profile schema
curl -X GET "http://localhost:8385/api/configurations/json_schema/Profile.yaml/latest/" -H "accept: application/json"

# Mentee schema
curl -X GET "http://localhost:8385/api/configurations/json_schema/Mentee.yaml/latest/" -H "accept: application/json"
```

- `../mentorhub_mongodb_api/configurator/dictionaries/Profile.*.yaml`
- `../mentorhub_mongodb_api/configurator/dictionaries/Mentee.*.yaml`
- Existing `docs/openapi.yaml` paths/schemas for `Profile` and `Encounter`, and the security scheme.

**External prerequisite**: the MongoDB `Profile` and `Mentee` dictionaries are current and the configurator serves the latest schemas at the URLs above. If the configurator is unavailable or the schemas are not current, set **Status** to `Blocked` and stop.

## Goals

- `docs/openapi.yaml` `Profile` component schema matches the latest `Profile.yaml` from the configurator (properties, types, descriptions, optionality).
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

_Reserved for the task execution agent._
