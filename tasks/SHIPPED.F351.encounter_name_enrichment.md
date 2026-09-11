# F351 – Encounter name enrichment for mentor and mentee

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F350_encounter_mutations_openapi`  
**Description:** Implement `mentor_name` and `mentee_name` lookup enrichment on Encounter documents in `src/services/encounter_service.py`. When returning encounter documents from any endpoint (by-id, list for mentee, create, or update), resolve `mentor_name` from the mentor's Profile `display_name` using `mentor_id`, and `mentee_name` from the mentee's Profile `display_name` using `mentee_id`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Service-to-Service and cross-collection lookup patterns
- `tasks/_PLANNING.md` — MongoIO only; outbound enrichment; do not call PyMongo directly
- `README.md` — Profile display identity is `display_name`
- `docs/openapi.yaml` — `mentor_name` and `mentee_name` properties on `Encounter` schema; `Profile` component schema has `display_name`
- `src/services/encounter_service.py` — subclass of shared EncounterService
- `src/services/profile_service.py` — Profile lookup and `display_name` resolution
- `src/routes/encounter_routes.py` — HTTP routes returning Encounter JSON
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

## Goals

- In `src/services/encounter_service.py`:
  - Add helper `_enrich_encounter(cls, encounter, mongo=None, config=None)`:
    - If `encounter` is `None` or not a dict, return `encounter`.
    - Retrieve `mentor_id` and `mentee_id` from `encounter`.
    - If `mentor_id` is present, look up the mentor document in `config.PROFILE_COLLECTION_NAME` via `mongo.get_document`.
      Set `encounter["mentor_name"] = mentor.get("display_name")` if profile found, else `None`.
    - If `mentee_id` is present, look up the mentee document in `config.PROFILE_COLLECTION_NAME` via `mongo.get_document`.
      Set `encounter["mentee_name"] = mentee.get("display_name")` if profile found, else `None`.
    - Return the modified encounter dictionary.
  - Add helper `_enrich_encounters(cls, encounters, mongo=None, config=None)`:
    - Enrich a list of encounter documents, optionally batching or caching Profile lookups to minimize database queries.
  - Override or wrap `get_encounter(cls, encounter_id, token, breadcrumb)`:
    - Call `super().get_encounter(encounter_id, token, breadcrumb)`.
    - Enrich and return the resulting encounter document.
  - Override or wrap `get_encounters_for_mentee(cls, mentee_id, token, breadcrumb, offset=0, size=20)`:
    - Call `super().get_encounters_for_mentee(mentee_id, token, breadcrumb, offset=offset, size=size)`.
    - Enrich and return the resulting encounter list.
  - In `update_encounter(cls, encounter_id, data, token, breadcrumb)`:
    - Ensure the returned updated document is enriched with `mentor_name` and `mentee_name`.
  - In `create_encounter(cls, data, token, breadcrumb)`:
    - Verify that when the route calls `get_encounter(encounter_id, token, breadcrumb)` after creation, the enriched document is returned.
- In `test/services/test_encounter_service.py`:
  - Add unit test asserting `get_encounter` returns `mentor_name` and `mentee_name` from Profile `display_name`.
  - Add unit test asserting `get_encounters_for_mentee` returns list of encounters with `mentor_name` and `mentee_name`.
  - Add unit test asserting `update_encounter` returns updated document with `mentor_name` and `mentee_name`.
  - Test graceful fallback when profile is missing (`None`) or has empty/blank `display_name`.
- In `test/routes/test_encounter_routes.py`:
  - Update route mock responses to include `mentor_name` and `mentee_name`.

### Craftsmanship Expectations

- Do **not** persist `mentor_name` or `mentee_name` into MongoDB (MongoDB `Encounter` schema has `additionalProperties: false`). This is purely an outbound read projection / enrichment.
- Use `MongoIO` (`get_document` or `get_documents`) for database queries. Never call PyMongo directly.
- Ensure enrichment handles both string IDs and BSON `ObjectId` values cleanly.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_encounter_service.py` — verify `mentor_name` and `mentee_name` presence and fallback behavior
  - `test/routes/test_encounter_routes.py` — verify routes return enriched payload
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml`

## Outputs

- `src/services/encounter_service.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

The agent must not update files outside this list.

## Execution Notes

1. Implemented `_enrich_encounter` and `_enrich_encounters` helpers in `src/services/encounter_service.py`:
   - Looks up mentor's and mentee's Profile documents in `config.PROFILE_COLLECTION_NAME` via `MongoIO.get_document`.
   - Sets `encounter["mentor_name"] = mentor.get("display_name") if mentor else None`.
   - Sets `encounter["mentee_name"] = mentee.get("display_name") if mentee else None`.
   - Caches lookups in `_enrich_encounters` to avoid duplicate queries for batch lists.
2. Overrode `get_encounter`, `get_encounters_for_mentee`, and `get_recent_encounter` to wrap superclass methods and enrich returned encounters.
3. Updated `update_encounter` to enrich returned document before return.
4. Added comprehensive unit tests in `test/services/test_encounter_service.py` verifying single document enrichment, missing profile fallback, batch list caching, and superclass delegation.
5. Formatted and verified with `pipenv run test` (163 passed) and `pipenv run lint` (clean).
