# F359 – Update Encounter schema in OpenAPI specification

**Status:** Shipped  
**Type:** Feature  
**Depends On:** none  
**Description:** Update the `Encounter` schema and response examples in `docs/openapi.yaml` to align with the updated Encounter dictionary from the schema server: add `actual` (`appointment` object with `from` and `to` date-time properties) and `no_show` (`boolean`), align `agenda` step pattern to `^[^\t\n]{0,255}$`, and update endpoint response examples.

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
- Running schema server endpoint: `http://localhost:8383/api/configurations/json_schema/Encounter.yaml/latest/`

### Schema Delta

From running schema server (`Encounter.yaml`) and MongoDB `Encounter` collection validator:

| Property | Previous OpenAPI | Target OpenAPI | Action |
| --- | --- | --- | --- |
| `_id` | `identifier` (24-hex string) | `identifier` (24-hex string) | Unchanged |
| `mentor_id` | `identifier` | `identifier` | Unchanged |
| `mentee_id` | `identifier` | `identifier` | Unchanged |
| `plan_id` | `identifier` | `identifier` | Unchanged |
| `appointment` | object (`from`, `to` date-time) | object (`from`, `to` date-time) | Unchanged |
| `actual` | **none** | object (`from`, `to` date-time), `additionalProperties: false` | Add ("When the encounter actually happened") |
| `no_show` | **none** | `boolean` | Add ("Flag indicating whether the encounter was a no-show") |
| `agenda` | array of `{ checked, step }` | array of `{ checked, step }` | Align `step` pattern to `'^[^\t\n]{0,255}$'` |
| `mentor_name` | string | string | Unchanged (API enrichment) |
| `mentee_name` | string | string | Unchanged (API enrichment) |
| `status` | enum: `[active, archived, complete, scheduled]` | enum: `[active, archived, complete, scheduled]` | Unchanged |
| `tldr` | string, pattern `^[^\t\n]{0,255}$` | string, pattern `^[^\t\n]{0,255}$` | Unchanged |
| `summary` | string, maxLength: 4096 | string, maxLength: 4096 | Unchanged |
| `transcript` | string, maxLength: 4096 | string, maxLength: 4096 | Unchanged |
| `created` | `$ref: '#/components/schemas/Breadcrumb'` | `$ref: '#/components/schemas/Breadcrumb'` | Unchanged |
| `saved` | `$ref: '#/components/schemas/Breadcrumb'` | `$ref: '#/components/schemas/Breadcrumb'` | Unchanged |

## Goals

- In `docs/openapi.yaml`:
  - **Align `Encounter` component schema**:
    - Add `actual` property:
      ```yaml
      actual:
        type: object
        description: When the encounter actually happened
        additionalProperties: false
        properties:
          from:
            type: string
            format: date-time
            description: When the scheduled appointment starts
          to:
            type: string
            format: date-time
            description: When the scheduled appointment ends
      ```
    - Add `no_show` property:
      ```yaml
      no_show:
        type: boolean
        description: Flag indicating whether the encounter was a no-show
      ```
    - In `agenda.items.properties.step`, update pattern from `'^[^\t\n]{1,255}$'` to `'^[^\t\n]{0,255}$'` to match schema server sentence definition.
    - Retain all other fields (`_id`, `mentor_id`, `mentee_id`, `plan_id`, `appointment`, `mentor_name`, `mentee_name`, `status`, `tldr`, `summary`, `transcript`, `created`, `saved`).
    - Keep `additionalProperties: false`.
    - Keep required list: `_id`, `created`, `saved`.
  - **Align endpoint documentation & examples**:
    - Update `GET /api/encounter` response items to include `actual` and `no_show` fields.
    - Update `GET /api/encounter/{EncounterId}` response example to include `actual` and `no_show`.
    - Update `POST /api/encounter/{EncounterId}/start` response example to show `actual.from` populated.
    - Update `POST /api/encounter/{EncounterId}/finish` response example to show `actual.from` and `actual.to` populated.

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
- **Contract Boundary Test**:
  - `pipenv run pytest test/e2e/test_boundaries.py::test_live_openapi_matches_list_and_aggregation_contracts`

## Outputs

- `docs/openapi.yaml`

The agent must not update files outside this list.

## Execution Notes

1. Updated `Encounter` component schema in `docs/openapi.yaml`:
   - Added `actual` object property with `from` and `to` date-time format properties and `additionalProperties: false`.
   - Added `no_show` boolean property.
   - Updated `agenda.items.properties.step.pattern` and `EncounterUpdate.agenda.items.properties.step.pattern` to `'^[^\t\n]{0,255}$'`.
   - Preserved `additionalProperties: false` and required fields `_id`, `created`, `saved`.
2. Validated YAML structure and parsed cleanly with YAML loader.
3. Verified `pipenv run lint` (clean, 50 files unchanged) and `pipenv run build`.
4. Verified contract boundary test `pytest test/e2e/test_boundaries.py::test_live_openapi_matches_list_and_aggregation_contracts` (PASSED 100%).
5. Verified unit test suite `pipenv run test` (190 passed).
