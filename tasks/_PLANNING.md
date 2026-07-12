# API Task Automation Framework - Planning

This folder contains coding tasks that an orchestration agent can execute, based on the context and instructions in each task file. This file is a guide for an agent that is helping to plan changes by creating task files to achieve a goal. Create tasks following the [naming conventions](#naming-conventions) and guides below. Before creating any task files you should review the following files for context:

- ../mentorhub/DeveloperEdition/standards/api_standards.md
- ../mentorhub_api_utils/README.md
- ./README.md
- ./tasks/_ORCHESTRATION.md
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
  - `STATUS.LNNN.short_task_name.md`
  - Examples:
    - `AS_NEEDED.T998.example_update_openapi.md`
    - `PENDING.L010.update_profile_openapi.md`
    - `RUNNING.L020.add_profile_field_tests.md`
    - `SHIPPED.L010.update_profile_openapi.md`

- **Path anchoring**
  - All paths in task files are relative to **this API repository root** (the directory that contains `Pipfile`).
  - Sibling repos (mentorhub umbrella, other APIs, SPAs) must all be sibling folders under a common parent.
  - Standards: `../mentorhub/DeveloperEdition/standards/api_standards.md`
  - Generated JSON schemas: `../mentorhub/Specifications/schemas/<Collection>.schema.json`
  - MongoDB configurator tasks (external): `../mentorhub_mongodb_api/Tasks/`
  - In-repo: `README.md`, `docs/openapi.yaml`, `src/...`, `test/...`, `tasks/...`

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

Reference: `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`, `../mentorhub/DeveloperEdition/standards/api_standards.md`, and shipped task `SHIPPED.L070.implement_plan_steps_service.md`.

## Sample task file

For a complete example of a well‑formed `Run as needed` task, see:

- `AS_NEEDED.T998.example_update_openapi.md`
