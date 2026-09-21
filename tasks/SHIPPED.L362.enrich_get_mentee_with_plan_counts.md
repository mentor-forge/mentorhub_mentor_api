# L362 – Enrich GET /mentee/{profile_id} with Plan Counts

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Add `plan_counts` to the `GET /mentee/{profile_id}` response so the SPA encounter detail page can retrieve plan counts `(library, now, next)` in a single mentee call, instead of making a separate call to the heavy profile-properties endpoint.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `README.md`
- `docs/openapi.yaml` — current `Mentee` schema and `GET /api/mentee/{profile_id}` spec
- `src/services/mentee_service.py` — current `get_mentee` implementation
- `src/services/profile_service.py` — `get_profile_properties` already calls `JourneyService.get_journey_progress`; reuse that logic
- `test/services/test_mentee_service.py`

### Background

The SPA encounter detail page needs to display plan counts `(library, now, next)` alongside the mentee name in the encounter card title bar. These counts come from `JourneyService.get_journey_progress(profile_id, token, breadcrumb)`, which is already called in `ProfileService.get_profile_properties` and returns `{"library": int, "now": int, "next": int}`. Currently `GET /mentee/{profile_id}` does not include this data, forcing the SPA to either call the expensive profile-properties endpoint or compute the counts client-side from raw journey data.

The fix is to call `get_journey_progress` inside `get_mentee` and append a `plan_counts` object to the response. No new collections or joins are needed.

## Goals

- `MenteeService.get_mentee` appends a `plan_counts` key to the returned document before returning it:
  ```python
  plan_counts = JourneyService.get_journey_progress(profile_id_str, token, breadcrumb)
  result["plan_counts"] = {
      "library": plan_counts.get("library", 0),
      "now":     plan_counts.get("now",     0),
      "next":    plan_counts.get("next",    0),
  }
  ```
  Use the string form of `profile_id` when calling `get_journey_progress` (consistent with how `profile_service.py` calls it).

- If `get_journey_progress` raises any exception, log a warning and set `plan_counts` to `{"library": 0, "now": 0, "next": 0}` — do **not** let a journey error fail the mentee GET.

- `docs/openapi.yaml` — update `Mentee` schema to include `plan_counts`:
  ```yaml
  plan_counts:
    type: object
    description: "Count of journey resources in each bucket for this mentee"
    properties:
      library:
        type: integer
        description: "Number of completed (library) resources"
        example: 15
      now:
        type: integer
        description: "Number of in-progress (now) resources"
        example: 2
      next:
        type: integer
        description: "Number of queued (next) resources"
        example: 30
    required: [library, now, next]
  ```
  Add `plan_counts` to `required: false` in the `Mentee` schema (it is always present but derived, not stored). Update the `GET /api/mentee/{profile_id}` response example to include `plan_counts`.

- Do **not** persist `plan_counts` to MongoDB — it is computed on read only. Do not add it to `MenteeUpdate`.

### Craftsmanship Expectations

- Import `JourneyService` inside the method (not at module top level) to avoid circular imports, consistent with the pattern in `profile_service.py`.
- `plan_counts` must not appear in `_default_document` or `update_mentee` — it is read-only and derived.
- Keep `additionalProperties: false` on the `Mentee` schema; add `plan_counts` as an explicit optional property.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests** — `pipenv run test`
  - Update `test/services/test_mentee_service.py`:
    - Mock `JourneyService.get_journey_progress` to return `{"library": 5, "now": 1, "next": 10}`.
    - Assert the returned document contains `plan_counts: {"library": 5, "now": 1, "next": 10}`.
    - Add a test for the error-fallback path: when `get_journey_progress` raises, assert `plan_counts` is `{"library": 0, "now": 0, "next": 0}` and the GET still succeeds.

- **Lint & build** — `pipenv run lint` + `pipenv run build`

- **OpenAPI validation** — `python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`

- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/api/mentee/{a_valid_profile_id}` — response includes `plan_counts`.
  - `curl -s http://localhost:8391/docs/openapi.yaml` — still served.

## Outputs

- `src/services/mentee_service.py` — append `plan_counts` in `get_mentee`.
- `test/services/test_mentee_service.py` — new tests for `plan_counts` happy path and error fallback.
- `docs/openapi.yaml` — `Mentee` schema updated with `plan_counts` property and example.

The agent must not update files outside this list.

## Execution Notes

- Updated `src/services/mentee_service.py`:
  - Enriched `MenteeService.get_mentee` to call `JourneyService.get_journey_progress(str(profile_id), token, breadcrumb)`.
  - Used lazy import of `JourneyService` inside `get_mentee` to avoid circular dependencies.
  - Handled exceptions safely: any journey retrieval exception logs a warning and defaults `plan_counts` to `{"library": 0, "now": 0, "next": 0}` without failing the request.
- Updated `docs/openapi.yaml`:
  - Added `plan_counts` object schema to `Mentee` with properties `library`, `now`, `next`, keeping it optional in `Mentee`.
  - Added response example to `GET /api/mentee/{profile_id}` including `plan_counts`.
  - Validated OpenAPI specification with Python YAML parser.
- Updated `test/services/test_mentee_service.py`:
  - Added `test_get_mentee_enriches_plan_counts` asserting plan counts enrichment.
  - Added `test_get_mentee_plan_counts_error_fallback` asserting resilient zero fallback on journey service errors.
- Test verification:
  - `pipenv run test`: 192 passed (100%).
  - `pipenv run lint`: Passed with black formatting.
  - `pipenv run build`: Passed clean.
  - Mandatory Pre-PR QA Gate:
    - `pipenv run container`: Built image `ghcr.io/mentor-forge/mentorhub_mentor_api:latest`.
    - `pipenv run api`: Restarted stack successfully.
    - `pipenv run e2e`: Passed 100% (51 passed, 2 skipped, 0 failed).
    - Verified live HTTP response on port 8391: `GET /api/mentee/{profile_id}` returns HTTP 200 with `plan_counts`.
