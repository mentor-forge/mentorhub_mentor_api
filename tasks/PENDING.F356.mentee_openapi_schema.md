# F356 – Update Mentee schema in OpenAPI specification

**Status:** Pending  
**Type:** Feature  
**Depends On:** none  
**Description:** Update the `Mentee` and `MenteeUpdate` schemas in `docs/openapi.yaml` to align with the simplified Mentee dictionary from the schema server: rename `description` to `summary`, remove `focus`, `homework`, `schedule`, `next_appointment`, and `name`, set `additionalProperties: false`, and align endpoint response examples.

## Path Anchoring

All paths are relative to **this API repository root** (the directory that contains `Pipfile`).

- Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
- In-repo: `docs/openapi.yaml`, `tasks/`

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `README.md`
- `docs/openapi.yaml`
- Running schema server endpoint: `http://localhost:8383/api/dictionaries/Mentee.0.1.0.yaml/`

### Schema Delta

From running schema server (`Mentee.0.1.0.yaml`) and MongoDB `Mentee` collection validator:

| Property | Previous OpenAPI | Target OpenAPI | Action |
| --- | --- | --- | --- |
| `_id` | `identifier` | `identifier` (24-hex string) | Unchanged |
| `name` | string | **none** | Remove from schema |
| `description` | sentence | **none** | Rename to `summary` |
| `summary` | **none** | `string`, pattern `^[^\t\n]{0,255}$` | Add ("Short summary of the mentoring relationship") |
| `focus` | sentence | **none** | Remove from schema |
| `homework` | markdown | **none** | Remove from schema |
| `schedule` | object | **none** | Remove from schema |
| `next_appointment` | date-time | **none** | Remove from schema |
| `notes` | markdown (4096) | `string`, maxLength: 4096 | Unchanged |
| `status` | enum: `[active, archived]` | enum: `[active, archived]` | Unchanged |
| `created` | `$ref: Breadcrumb` | `$ref: Breadcrumb` | Unchanged |
| `saved` | `$ref: Breadcrumb` | `$ref: Breadcrumb` | Unchanged |

## Goals

- In `docs/openapi.yaml`:
  - **Align `Mentee` component schema**:
    - Remove `name`, `description`, `focus`, `homework`, `schedule`, and `next_appointment`.
    - Add `summary` property: type `string`, description `"Short summary of the mentoring relationship"`, pattern `'^[^\t\n]{0,255}$'`, example `"Short summary of the mentoring relationship"`.
    - Retain `_id`, `status`, `notes` (maxLength: 4096), `created`, and `saved`.
    - Ensure `additionalProperties: false`.
    - Required fields remain: `_id`, `created`, `saved`.
  - **Align `MenteeUpdate` component schema**:
    - Remove `name`, `description`, `focus`, `homework`, `schedule`, and `next_appointment`.
    - Allow updating `summary`, `notes`, and `status`.
    - Ensure `additionalProperties: false`.
  - **Align endpoint documentation & examples**:
    - Update `GET /api/mentee/{profile_id}` response description and examples to reflect `summary` and `notes`.
    - Update `PATCH /api/mentee/{profile_id}` request body description and examples to demonstrate updating `summary` and `notes`.

### Craftsmanship Expectations

- Maintain strict parity with the authoritative dictionary definition from the schema server.
- Ensure `docs/openapi.yaml` remains fully valid OpenAPI 3.0.3 without unresolved `$ref` references.

## Testing Expectations

Run all commands from this API repository root:

- **Validation**:
  - `python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
- **Lint & Build**:
  - `pipenv run lint`
  - `pipenv run build`

## Outputs

- `docs/openapi.yaml`

The agent must not update files outside this list.

## Execution Notes

