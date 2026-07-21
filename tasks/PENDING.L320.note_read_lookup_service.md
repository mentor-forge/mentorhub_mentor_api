# L320 – Read-only Note lookup service

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Add a lightweight, read-only `NoteService` to this repo exposing `get_notes_for_resource(resource_id, token, breadcrumb)`. This is the note-read dependency consumed by the aggregation detail endpoint (L330). No create/update/delete and no HTTP route are added in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `MongoIO` read helpers (`get_documents`)
- `api_utils.Config` — `NOTE_COLLECTION_NAME` (default `"Note"`)

Reference implementation to port from (already shipped in the mentee API):

- `../mentorhub_mentee_api/src/services/note_service.py` — source of `get_notes_for_resource` (port the read path only; omit `create_note`/`get_note` unless needed by L330)
- `../mentorhub_mentor_api/src/services/resource_service.py` — this repo's existing service conventions (logging, exceptions, `MongoIO`/`Config` usage)

## Goals

- **New service** `src/services/note_service.py`:
  - `get_notes_for_resource(resource_id, token, breadcrumb)`:
    - Open to any authenticated user (no additional role gate).
    - Validate `resource_id` is a valid MongoDB `ObjectId`; raise `HTTPBadRequest` otherwise.
    - Read via `MongoIO.get_documents(config.NOTE_COLLECTION_NAME, match={"resource_id": <ObjectId>}, sort_by=[("created.at_time", DESCENDING)])`.
    - Return the list of Note documents (empty list when none).
    - Log a summary line including note count, `resource_id`, and `user_id`.
    - Wrap unexpected errors in `HTTPInternalServerError`; re-raise `HTTPBadRequest`.
  - **MongoIO-only**: all MongoDB I/O goes through `MongoIO` (no direct PyMongo collection access), per `_PLANNING.md`.
  - Do **not** add an HTTP route or blueprint in this task.
- **Unit tests** `test/services/test_note_service.py` (new):
  - Returns notes for a resource (mocked `MongoIO`), including sort/match arguments.
  - Returns empty list when no notes exist.
  - Invalid `resource_id` raises `400`.

## Testing Expectations

Run all commands from the **API repository root** (`../mentorhub_mentor_api`).

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_note_service.py` — read lookup, empty result, invalid id
- **Build**
  - `pipenv run build`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/note_service.py` — **new** read-only `NoteService.get_notes_for_resource`
- `test/services/test_note_service.py` — **new** unit tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
