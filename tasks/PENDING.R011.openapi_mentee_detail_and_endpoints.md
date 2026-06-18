# R011 – Define mentee detail view + Mentee endpoints in OpenAPI

**Status**: Pending  
**Task Type**: Docs  
**Run Mode**: Sequential  <!-- options: Sequential | Run as needed -->

## Goal

Update `mentorhub_mentor_api/docs/openapi.yaml` to describe (contract-first) the
mentee detail view and the new Mentee endpoints, before/independent of the
implementation (see R012):

- `GET /api/profile/{ProfileId}` returns a composite **mentee detail** view
  (Profile + mentee notes + list of Encounters) instead of the bare Profile.
- New `GET /api/mentee/{profile_id}` and `PATCH /api/mentee/{mentee_id}`
  endpoints.

## Context / Input files

These files must be treated as **inputs** and read before implementation:

- `mentorhub_mentor_api/docs/openapi.yaml` – existing paths/schemas (Profile,
  Encounter, responses, security schemes)
- `mentorhub_mongodb_api/configurator/dictionaries/Profile.0.1.0.yaml`
- `mentorhub_mongodb_api/configurator/dictionaries/Encounter.0.1.0.yaml`
- `mentorhub_mongodb_api/configurator/dictionaries/Note.0.1.0.yaml` (current
  backing store for mentee notes)

## Requirements

- **`GET /api/profile/{ProfileId}`**
  - Update summary/description to the read-only mentee detail view; keep the
    `mentor` or `admin` role requirement and the `401`/`403`/`404`/`500`
    responses.
  - `200` response body → new `MenteeDetail` schema.
- **`GET /api/mentee/{profile_id}`**
  - Read-only; requires `mentor` or `admin`.
  - Returns `MenteeNotes`; documents that a default doc is created if none
    exists (so the UI always gets a valid document).
  - Responses: `200`, `401`, `403`, `500`.
- **`PATCH /api/mentee/{mentee_id}`**
  - Requires `mentor` or `admin`; request body `MenteeNotesUpdate`.
  - `_id`, `created`, `saved` are system-managed and rejected.
  - Responses: `200`, `401`, `403`, `404`, `500`.
- **Schemas to add**
  - `MenteeNotes` – the mentee-notes document (based on `Note`: `_id`,
    `profile_id`, `note`, `status`, `created`, `saved`).
  - `MenteeNotesUpdate` – patchable fields only (e.g. `note`, `status`).
  - `MenteeDetail` – `{ profile: Profile, notes: MenteeNotes, encounters:
    [Encounter, ...] }`.
- Add a `Mentee` tag for the new endpoints.

## Testing expectations

- No runtime tests for this task; validate the spec instead:
  - YAML parses (`python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`).
  - No dangling `$ref`s (every `$ref` resolves to a defined component).
  - Optional: render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Packaging / build checks

- N/A (documentation only). Ensure the spec is valid so the explorer route and
  any spec-driven tooling keep working.

## Dependencies / Ordering

- Should run **before**: `R012` (implementation should match this contract).
- Coordinate with Mary's schema/test-data updates: if a dedicated `Mentee`
  schema replaces the `Note`-backed approach, update `MenteeNotes` accordingly.
- Branch: `dashboard-refactor` (mentor_api).

## Open questions for review

1. Should `GET /api/profile/{ProfileId}` change shape to the composite `MenteeDetail`, or should the composite live only behind the new `/api/mentee` endpoints (leaving the Profile endpoint unchanged)?
2. Mentee notes are currently modeled on the existing `Note` schema. If Mary introduces a dedicated `Mentee` schema, `MenteeNotes` should track that instead — confirm which schema is the source of truth before finalizing.

## Change control checklist

- [ ] Reviewed all **Context / Input files**.
- [ ] Updated `GET /api/profile/{ProfileId}` to the `MenteeDetail` response.
- [ ] Added `GET /api/mentee/{profile_id}` and `PATCH /api/mentee/{mentee_id}`.
- [ ] Added `MenteeNotes`, `MenteeNotesUpdate`, `MenteeDetail` schemas + `Mentee` tag.
- [ ] Validated YAML parses and all `$ref`s resolve.
- [ ] Created a scoped commit referencing this task ID.

## Implementation notes (to be updated by the agent)

**Summary of changes**
- _TBD_

**Testing results**
- Spec validation: _command(s) run, high-level outcome_

**Follow-up tasks**
- _Revisit `MenteeNotes` if Mary introduces a dedicated Mentee schema._
