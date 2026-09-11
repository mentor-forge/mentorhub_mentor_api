# F354 – Start and Finish Encounter mutations

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F353_schedule_encounters_mutation`  
**Description:** Implement Start Encounter and Finish Encounter lifecycle mutations. Add `start_encounter` and `finish_encounter` in `EncounterService` and routes `POST /api/encounter/<encounter_id>/start` and `POST /api/encounter/<encounter_id>/finish`. Starting an encounter verifies the mentee's sponsor organization has available customer subscription balance, transitions status to `active`, logs an event via `EventService.create_event`, and decrements the customer subscription balance. Finishing an encounter transitions status from `active` to `complete`. Both mutations return enriched encounter documents.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Service-to-service calls; stateless business logic and RBAC
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `docs/openapi.yaml` — `POST /api/encounter/{EncounterId}/start` and `finish` endpoints
- `src/services/encounter_service.py`
- `src/services/event_service.py` — `EventService.create_event`
- `src/services/profile_service.py`
- `src/routes/encounter_routes.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`
- MongoDB schemas for Customer and Event (verify from running configurator):
  ```bash
  curl -s -X GET "http://localhost:8383/api/configurations/json_schema/Customer.yaml/latest/" -H "accept: application/json"
  curl -s -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
  ```

## Goals

- In `src/services/encounter_service.py`:
  - Add helper `_verify_and_decrement_subscription(cls, mentee_id, mongo, config, breadcrumb)`:
    - Look up the mentee's Profile from `config.PROFILE_COLLECTION_NAME` using `mentee_id`.
      If profile is not found or missing `customer_id`, raise `HTTPForbidden("Mentee has no associated customer")`.
    - Retrieve `customer_id = profile["customer_id"]`.
    - Look up the Customer from `config.CUSTOMER_COLLECTION_NAME` via `mongo.get_document(config.CUSTOMER_COLLECTION_NAME, str(customer_id))`.
      If customer is not found, raise `HTTPForbidden(f"Customer {customer_id} not found")`.
    - Inspect `customer.get("subscriptions", [])`:
      - Find an active subscription (`sub.get("status") == "active"`).
      - Check if `sub.get("free_encounters_remaining", 0) > 0` (or positive available encounters balance).
      - If no subscription has available balance, raise `HTTPForbidden("Insufficient subscription balance to start encounter")`.
      - Decrement `free_encounters_remaining` by 1 on the qualifying subscription.
    - Persist the updated subscriptions array on Customer via:
      `mongo.update_document(config.CUSTOMER_COLLECTION_NAME, document_id=str(customer_id), set_data={"subscriptions": subscriptions, "saved": breadcrumb})`.
  - Add `start_encounter(cls, encounter_id, token, breadcrumb)`:
    - Write permission check: caller must be owning mentor or admin (`_check_permission_write(token, "update", breadcrumb, encounter=encounter)`).
    - Retrieve encounter via `mongo.get_document(config.ENCOUNTER_COLLECTION_NAME, encounter_id)`.
      If not found, raise `HTTPNotFound(f"Encounter {encounter_id} not found")`.
    - Verify current status: encounter `status` must be `"scheduled"`.
      If status is already `"active"`, `"complete"`, or `"archived"`, raise `HTTPForbidden(f"Cannot start encounter: status is '{encounter.get('status')}', expected 'scheduled'")`.
    - Call `cls._verify_and_decrement_subscription(encounter.get("mentee_id"), mongo, config, breadcrumb)`.
    - Update encounter status to `"active"` with `saved: breadcrumb` via `mongo.update_document`.
    - Log event via `EventService.create_event`:
      ```python
      from src.services.event_service import EventService
      EventService.create_event(
          {
              "type": getattr(config, "EVENT_TYPE_ENCOUNTER", "encounter"),
              "context": {
                  "encounter_id": str(encounter_id),
                  "mentor_id": str(encounter.get("mentor_id")),
                  "mentee_id": str(encounter.get("mentee_id")),
              },
          },
          token,
          breadcrumb,
      )
      ```
    - Return the enriched updated encounter document.
  - Add `finish_encounter(cls, encounter_id, token, breadcrumb)`:
    - Write permission check: caller must be owning mentor or admin (`_check_permission_write(token, "update", breadcrumb, encounter=encounter)`).
    - Retrieve encounter via `mongo.get_document`. If not found, raise `HTTPNotFound`.
    - Verify current status: encounter `status` must be `"active"`.
      If status is not `"active"`, raise `HTTPForbidden(f"Cannot finish encounter: status is '{encounter.get('status')}', expected 'active'")`.
    - Update encounter status to `"complete"` with `saved: breadcrumb` via `mongo.update_document`.
    - Return the enriched updated encounter document.
- In `src/routes/encounter_routes.py`:
  - Mount `POST /api/encounter/<encounter_id>/start`:
    - Call `create_flask_token()`, `create_flask_breadcrumb(token)`.
    - Call `EncounterService.start_encounter(encounter_id, token, breadcrumb)`.
    - Return `jsonify(encounter), 200`.
  - Mount `POST /api/encounter/<encounter_id>/finish`:
    - Call `create_flask_token()`, `create_flask_breadcrumb(token)`.
    - Call `EncounterService.finish_encounter(encounter_id, token, breadcrumb)`.
    - Return `jsonify(encounter), 200`.
- In `test/services/test_encounter_service.py`:
  - Test `start_encounter`:
    - Successful transition from `"scheduled"` to `"active"`.
    - Customer subscription `free_encounters_remaining` decremented and saved.
    - Event created via `EventService.create_event`.
    - Returned encounter is enriched with `mentor_name` and `mentee_name`.
    - Fails with 403 when customer has zero subscription balance.
    - Fails with 403 when mentee profile has no customer or customer not found.
    - Fails with 403 when caller is non-owning mentor.
    - Fails with 404 when encounter does not exist.
    - Fails with 403 when encounter status is not `"scheduled"`.
  - Test `finish_encounter`:
    - Successful transition from `"active"` to `"complete"`.
    - Returned encounter is enriched with `mentor_name` and `mentee_name`.
    - Fails with 403 when encounter status is not `"active"`.
    - Fails with 403 when caller is non-owning mentor.
    - Fails with 404 when encounter does not exist.
- In `test/routes/test_encounter_routes.py`:
  - Add tests for `POST /api/encounter/<encounter_id>/start` and `POST /api/encounter/<encounter_id>/finish` (200 success, 403 forbidden, 404 not found).

### Craftsmanship Expectations

- Inbound write RBAC, subscription verification, state transitions, and event logging belong in `EncounterService`.
- Use `EventService.create_event` for event recording.
- All database modifications route through `MongoIO`.
- Return fully enriched documents with `mentor_name` and `mentee_name`.

## Testing Expectations

Run all commands from this API repository root:

- **Unit tests**:
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_encounter_service.py` — verify start and finish logic, subscription decrement, event logging, status transitions
  - `test/routes/test_encounter_routes.py` — verify HTTP endpoints return 200, 403, 404
- **Packaging verification**:
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8391/docs/openapi.yaml`

## Outputs

- `src/services/encounter_service.py`
- `src/routes/encounter_routes.py`
- `test/services/test_encounter_service.py`
- `test/routes/test_encounter_routes.py`

The agent must not update files outside this list.

## Execution Notes

1. Implemented `_verify_and_decrement_subscription` in `src/services/encounter_service.py`:
   - Resolved customer from mentee's Profile `customer_id`.
   - Verified active subscription exists with `free_encounters_remaining > 0`.
   - Decremented `free_encounters_remaining` and persisted on Customer via `MongoIO.update_document`.
2. Implemented `start_encounter`:
   - Enforced owner/admin RBAC and `"scheduled"` status guardrail.
   - Decremented subscription balance, transitioned status to `"active"`, logged event via `EventService.create_event`, and returned enriched document.
3. Implemented `finish_encounter`:
   - Enforced owner/admin RBAC and `"active"` status guardrail.
   - Transitioned status to `"complete"` and returned enriched document.
4. Mounted `POST /api/encounter/<encounter_id>/start` and `POST /api/encounter/<encounter_id>/finish` on blueprint in `src/routes/encounter_routes.py`.
5. Added unit tests in `test/services/test_encounter_service.py` and route tests in `test/routes/test_encounter_routes.py`.
6. Verified with `pipenv run format`, `pipenv run test` (190 passed), and `pipenv run lint`.
