# API Task Automation Framework - Planning

This folder contains coding tasks that an orchestration agent can execute, based on the context and instructions in each task file. This file is a guide for an agent that is helping to plan changes by creating task files to achieve a goal. Create tasks following the [naming conventions](#naming-conventions) and guides below. When planning, only create tasks, do not execute any tasks, and do not change any files outside of the tasks folder. 

- **Path anchoring**
  - All paths in task files are relative to **this API repository root** (the directory that contains `Pipfile`).
  - Sibling repos must all be sibling folders under a common parent.
  - Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
  - In-repo: `README.md`, `docs/openapi.yaml`, `src/...`, `test/...`, `tasks/...`

- **Context** Before creating any task files you should review the following files for context:
- ../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md
- ../mentorhub/DeveloperEdition/standards/api_standards.md
- ../mentorhub_api_utils/README.md
- ./README.md
- ./tasks/_ORCHESTRATE.md
- ./tasks/_PLANNING.md (this file)

## Task File Layout

Each task file must contain the following sections under H1 and H2 headings.

- Under the top H1 task header:
  - Each task file should declare `Status:` **inside the file**, and also encode the status in the **filename prefix** so tasks are visually grouped in the IDE.
  - **Lifecycle statuses (in‑file)**:
    - `Pending`: Not yet started.
    - `Running`: Work is currently being done in the active session.
    - `Blocked`: Waiting on some external dependency or decision.
    - `Shipped`: Implemented, tested, and committed as per the change control process.
    - `Run as needed`: Not part of the main long‑running sequence; to be run manually or opportunistically.
  - **Filename status prefixes (for grouping)**:
    - `AS_NEEDED.` – Tasks that should **not** be part of the main long‑running sequence.
    - `BLOCKED.` – Tasks currently blocked.
    - `PENDING.` – Tasks that are ready to be picked up when their turn comes.
    - `RUNNING.` – (Optional) Tasks currently being executed in this session.
    - `SHIPPED.` – Tasks that are fully implemented and completed.
  - **Type**: `Feature` | `Defect` to describe why we are running this task
  - **Depends On**: `L010_update_profile_openapi` the required predecessor task **in this repo**, or `none` for parallel tasks
  - **Description**: A brief human description of the task.

- Under a **Context** H2 header:
  - A list of context files. This list should always include:
    - `../mentorhub/DeveloperEdition/standards/api_standards.md`
    - `tasks/README_API.md`
    - `README.md`
  - Any other input files for the execution of the task.
  - `AS_NEEDED` tasks may include a **Parameters (edit before running)** subsection here for values to customize before promoting to `Pending`.

- Under a **Goals** H2 header:
  - A list of desired outcomes for the task.
  - Each item should describe the outcome (e.g. "OpenAPI `Profile` schema includes `full_name`").

- Under a **Testing Expectations** H2 header:
  - Can include the creation of new tests for new features.
  - Can include changing existing tests because of modified features.
  - Should always include a description of the tests that should be used to verify completion.
  - In this repo, that typically means some combination of:
    - `pipenv run install` — refresh dependencies after `Pipfile` / lockfile changes (CodeArtifact auth; run `mh` first if needed)
    - `pipenv run test` — unit tests (pytest, excludes `@pytest.mark.e2e`)
    - `pipenv run lint` — format check (`black --check`)
    - `pipenv run build` — compile Python sources
    - `pipenv run dev` — run API dev server locally (for manual or E2E verification)
    - `pipenv run e2e` — end-to-end tests against a running API (long running)
  - Should always include the **Packaging verification** step:
    - `pipenv run container` — build the API container image
    - `pipenv run api` — run db + API containers
    - `pipenv run e2e` — E2E tests against the containerized API (or curl verification of `/docs/openapi.yaml` when appropriate)
  - All test files should be identified in **Outputs** (below).

- Under an **Outputs** H2 header:
  - A list of the files that will be created/updated/moved/renamed/etc.
  - `file_name.py` will be updated to support `<Goal>`
  - List all files including new files to be created.
  - The agent will not update files not listed.

- Under an **Execution Notes** H2 header:
  - Reserved for the task execution agent to record plan, commands run, test results, and follow-ups.

## Naming Conventions
- **Recommended filename pattern**:
  - `STATUS.LNNN.short_task_name.md` where L is (F)eature or (D)efect, and NNN is a serial task number. Increment task numbers by 1. When planning, create only PENDING status tasks. 
  - Examples:
    - `PENDING.D001.example_defect.md`
    - `PENDING.F010.update_profile_openapi.md`
    - `PENDING.F011.add_profile_field_tests.md`
    - `PENDING.F012.update_profile_openapi.md`

## External repository boundaries

Task planning and execution in **this API repo** (`mentorhub_mentor_api`) must not read or depend on other sibling repositories for input context, except:

- **`../mentorhub`** — platform standards and shared documentation (e.g. `DeveloperEdition/standards/api_standards.md`).
- **`../mentorhub_api_utils`** — shared Python utilities used by domain APIs (e.g. `MongoIO`, Flask helpers, `README.md`).

Do **not** reference paths under `mentorhub_mongodb_api`, other domain API repos, SPAs, or CloudFormation repos in task **Context** or **Goals**. If work in another repository is a prerequisite, describe it as an **external prerequisite** in prose (e.g. “MongoDB dictionary must include field X”) and set **Status** to `Blocked` until a human confirms it — do not link to or read files in that repo.

## MongoDB dictionary schemas

**Definitive** MongoDB collection/dictionary schema information must come from the **running MongoDB configurator service** (`mentorhub_mongodb_api`), not from files in the `mentorhub_mongodb_api` repository.

Start the backing database if needed (`pipenv run db`), then fetch the latest JSON schema with `curl`:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/<Dictionary>.yaml/latest/" -H "accept: application/json"
```

Replace `<Dictionary>` with the collection name (e.g. `Path`, `Resource`, `Note`). Use this response as the source of truth when updating `docs/openapi.yaml` component schemas or when implementing service projections. Do **not** use deprecated paths under `../mentorhub/Specifications/schemas/`.

If the configurator is unavailable, set the task **Status** to `Blocked` and stop — do not fall back to dictionary YAML files in the `mentorhub_mongodb_api` repo.

## Dependency management

Domain APIs resolve `api-utils` and other packages from **AWS CodeArtifact**. When a task bumps or adds dependencies in `Pipfile` / `Pipfile.lock`, the execution agent must install them with:

```bash
pipenv run install
```

Do **not** use bare `pipenv install` or `pipenv install --dev` in task instructions — those skip the repo’s CodeArtifact auth wrapper (`scripts/pipenv-install.sh`). Run `mh` once per shell session before `pipenv run install` if CodeArtifact credentials are not already available (see `README.md` and `../mentorhub/DeveloperEdition/standards/api_standards.md`).

Task **Testing Expectations** and **Goals** should call out `pipenv run install` whenever `Pipfile` or `Pipfile.lock` changes.

## MongoDB access

Service code must route all MongoDB I/O through **`MongoIO`** (`api_utils.mongo_utils.mongo_io`) — use `get_document`, `get_documents`, `create_document`, `update_document`, and `upsert_document` as appropriate. Do **not** call PyMongo directly (for example `mongo.get_collection(...)` followed by `collection.find`, `find_one`, `insert_one`, or similar).

When planning or reviewing tasks, include this rule in **Context** or **Goals** for any work that touches `src/services/`. If a task cannot comply without an upstream `api_utils` change, document the gap and any temporary exception in that task’s **Execution Notes** — not here.

Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`, `../mentorhub/DeveloperEdition/standards/api_standards.md`, and shipped task `SHIPPED.L070.refactor_services_to_mongoio.md`.
