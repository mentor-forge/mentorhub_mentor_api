# L060 – Update OpenAPI Plan schema for `steps`

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Sync the `docs/openapi.yaml` Plan schemas to the Plan data dictionary, exposing the list field the SPA Plan editor needs. The data dictionary stores this list as `checklist` (`additional_properties: false`), but per the agreed API contract it is exposed in the API as `steps` (storage `checklist` ⇄ API `steps`). This task is contract-only; the service mapping/validation is L070.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/README.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- `../mentorhub_mongodb_api/configurator/dictionaries/Plan.0.1.0.yaml` — authoritative Plan data schema. The list field is `checklist` (`type: array`, items `sentence`), described as "a list of things a mentor might want to do during an encounter".
- `../mentorhub/Specifications/features.md` lines 39–42 (SPA Plan list/detail) and line 62 (Plan API: "update Plan endpoints to latest schema").
- House style for an array-of-sentence property: the `Profile.goals` schema in `docs/openapi.yaml` (`type: array` → `items: { type: string, pattern: '^[^\t\n]{0,255}$' }`).
- Latest schema when the configurator is running on port `8383`:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Plan.yaml/latest/" -H "accept: application/json"
```

**Contract decision (confirmed with developer):** field is stored as `checklist` and exposed in the API as `steps`. Mongo `additionalProperties: false` would reject a literal `steps` document, so the API↔storage mapping lives in the service layer (L070); the spec describes the API surface (`steps`).

## Goals

- `Plan` schema gains a `steps` property: `type: array`, `items` are non-empty sentences (`type: string`, `pattern: '^[^\t\n]{1,255}$'`), with a description noting it is stored as `checklist`.
- `PlanInput` and `PlanUpdate` gain the same `steps` property so create/update can set the list.
- `GET /api/plan` (list) and `GET /api/plan/{PlanId}` continue to return `Plan` (which now includes `steps`); the SPA derives the step count from `steps.length`.
- Existing `401`/`403`/`404`/`500` responses and `additionalProperties: false` on `Plan` are preserved; no RBAC wording change in this task.
- The spec is valid: it parses and every `$ref` resolves.

## Testing Expectations

Documentation/contract task; validate the spec rather than runtime behavior.

- Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
- No dangling `$ref`s — every `$ref` resolves to a defined component.
- `pipenv run lint`

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add `steps` to `Plan`, `PlanInput`, and `PlanUpdate`.

The agent must not update files outside this list.

## Execution Notes

**Summary of changes** (`docs/openapi.yaml` only):
- Added a `steps` property to `Plan`, `PlanInput`, and `PlanUpdate`: `type: array`, `items` are non-empty sentences (`type: string`, `pattern: '^[^\t\n]{1,255}$'`). Description notes it is stored in MongoDB as `checklist`.
- Followed the existing `Profile.goals` array-of-sentence house style. Preserved `Plan.additionalProperties: false`, required list, and existing responses; no RBAC wording change.

**Testing results**
- `yaml.safe_load(open('docs/openapi.yaml'))` parses — OK.
- `$ref` check: 30 unique schema refs, 0 dangling.
- `steps` confirmed present in `Plan`, `PlanInput`, `PlanUpdate`.

**Follow-ups**
- Storage↔API mapping (`steps` ⇄ `checklist`) and input validation implemented in L070.
- Pattern is `{1,255}` (non-empty) — slightly tighter than the dictionary's `sentence` (`{0,255}`); intentional since an empty step is meaningless.
