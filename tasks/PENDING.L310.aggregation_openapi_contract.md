# L310 – Aggregation OpenAPI contract (Note, ResourceAggregation, AggregationDetail)

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Add the OpenAPI contract for a new `GET /api/aggregation/{resource_id}` endpoint that returns Resource_Aggregation metrics together with the Notes for that resource. This task only updates `docs/openapi.yaml` (schemas + path); the service and route are implemented in L330.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — this repo's current OpenAPI document (target of this task)

Reference implementation to port from (already shipped in the mentee API):

- `../mentorhub_mentee_api/docs/openapi.yaml` — source of `Note`, `ResourceAggregation`, and `AggregationDetail` schemas and the `getAggregationDetail` path/operation
- `../mentorhub_mentee_api/tasks/SHIPPED.L050.aggregation_service_and_route.md` — describes the `{ aggregation, notes }` contract
- Configurator schemas (start `pipenv run db` if needed) to confirm field shapes:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Note.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource_Aggregation.yaml/latest/" -H "accept: application/json"
```

## Goals

- `docs/openapi.yaml` component schemas include (ported/aligned from the mentee API and the generated JSON schemas):
  - `Note` — the Note document shape (fields, types, descriptions, optionality).
  - `ResourceAggregation` — the Resource_Aggregation document shape (`note_count`, `completions`, `hits`, `rating_count`, `rating_sum`, `duration`, breadcrumbs, `_id`).
  - `AggregationDetail` — object with:
    - `aggregation`: `$ref` `#/components/schemas/ResourceAggregation`
    - `notes`: array of `#/components/schemas/Note`
- `docs/openapi.yaml` declares an `Aggregation` tag (and a `Note` schema/tag as needed) consistent with existing tag style.
- `docs/openapi.yaml` defines the path `GET /api/aggregation/{resource_id}`:
  - `operationId: getAggregationDetail`
  - `resource_id` path parameter (string, MongoDB ObjectId).
  - Requires bearer auth consistent with other endpoints in this document.
  - `200` response body `$ref` `#/components/schemas/AggregationDetail`.
  - Error responses (`400`, `401`, etc.) consistent with existing endpoints in this document.
- The document remains valid OpenAPI and is served by the packaged API at `/docs/openapi.yaml`.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Lint / build**
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify OpenAPI is served and parses:
    - `curl -s http://localhost:8391/docs/openapi.yaml | head`
    - Confirm `AggregationDetail`, `ResourceAggregation`, `Note`, and the `getAggregationDetail` path are present.

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add `Note`, `ResourceAggregation`, `AggregationDetail` schemas; add `Aggregation` tag; add `GET /api/aggregation/{resource_id}` path/operation.

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
