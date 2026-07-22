# L320 – Read-only Note lookup service (thin wrapper over `api_utils.services.NoteService`)

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Add a lightweight, read-only local `NoteService` to this repo exposing `get_notes_for_resource(resource_id, token, breadcrumb)`. This is the note-read dependency consumed by the aggregation detail endpoint (L330). The read behavior already lives upstream in `api_utils.services.NoteService` (shipped in the pinned `api-utils==0.5.1`); this task adds a thin local wrapper that **delegates** to it, matching this repo's existing harvested-service convention. No create/update/delete and no HTTP route are added in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `api_utils.services.NoteService` — shared read implementation to delegate to (`get_notes_for_resource`, `list_all_notes_for_resource`), shipped in `api-utils==0.5.1`
- `src/services/resource_service.py` — this repo's established thin-wrapper convention over `api_utils.services` (delegation + local-only pieces, logging, exceptions)

> **Note**: The read/validate/MongoIO logic is already harvested upstream — do **not** port it from `../mentorhub_mentee_api/src/services/note_service.py`. `api_utils.services.NoteService.get_notes_for_resource` already validates the `resource_id` ObjectId (→ `HTTPBadRequest`), matches `{"resource_id": <ObjectId>}`, sorts `created.at_time` DESC by default, is MongoIO-only, and returns `[]` when none exist.

## Goals

- **New service** `src/services/note_service.py`:
  - Import the shared service: `from api_utils.services import NoteService as SharedNoteService`.
  - Expose a local `NoteService` class with:
    - `get_notes_for_resource(resource_id, token, breadcrumb)`:
      - Open to any authenticated user (no additional role gate).
      - **Delegate** to `SharedNoteService.get_notes_for_resource(resource_id, token, breadcrumb)` (the shared service handles ObjectId validation → `HTTPBadRequest`, the `{"resource_id": <ObjectId>}` match, the `created.at_time` DESC sort, and the empty-list case).
      - Return the list of Note documents (empty list when none).
  - **No local MongoDB access**: this wrapper must not call `MongoIO` or PyMongo directly — all storage I/O is reached through the shared `api_utils.services.NoteService`, per `_PLANNING.md`.
  - Do **not** add an HTTP route or blueprint in this task.
- **Unit tests** `test/services/test_note_service.py` (new):
  - `get_notes_for_resource` delegates to `api_utils.services.NoteService.get_notes_for_resource` with the correct arguments and returns its result (mock the shared service).
  - Empty result passes through unchanged.
  - `HTTPBadRequest` raised by the shared service for an invalid `resource_id` propagates (re-raised, not swallowed).
  - Deep MongoIO behavior (ObjectId encoding, sort/match construction) is **not** re-tested here — it is covered by upstream `api_utils` tests.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_note_service.py` — delegation, empty result, invalid-id propagation
- **Build**
  - `pipenv run build`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/note_service.py` — **new** read-only `NoteService.get_notes_for_resource` delegating to `api_utils.services.NoteService`
- `test/services/test_note_service.py` — **new** unit tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
