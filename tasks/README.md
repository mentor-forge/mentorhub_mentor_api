# API Task Automation Framework

This folder contains coding tasks that an agent can execute, based on the context and instructions in each task file. All of these tasks will only make changes in this API repo. The agent will orchestrate execution of all Pending Tasks to implement a Feature.

## Orchestration model: Feature Workflow

Before starting the workflow, check to make sure you are not on the main branch, and that you can push on the branch you are on. If you fail this test, pause and ask the developer how you should proceed, and then select or create a branch as instructed before starting the first task.

Now orchestrate all Pending Tasks as outlined below. Use an **orchestration agent** that spawns a **fresh agent per task**:

1. **Orchestrator** discovers all tasks, respects dependencies, and determines execution order.
   - **Task Selection**: Select only `PENDING.*` tasks.
   - **Execution order**: Review all PENDING tasks and order dependencies first.
   - Schedule **concurrent** agents if no dependencies exist.
2. **For each task**, the orchestrator launches a new agent with:
   - The task file path
   - Any outputs from prior tasks (e.g. "L010 complete; Profile schema updated in openapi.yaml")
3. **Sub-agent** executes only that task: read context, implement, test, update task notes.
4. **Commit Changes**: The orchestrator is responsible for a commit, with a meaningful message, and a push.
5. **Mark Shipped** by updating the task status, and renaming the task file like `SHIPPED.L010_update_profile_openapi.md`.
6. **Orchestrator** after the commit, moves to the next task.

**Task Failure Case**: In the event a task fails, execution should halt and the developer should receive a summary of the current state and error condition that caused the failure.

**All Tasks Complete**: Once all tasks have successfully completed, the orchestration agent should create a Pull Request in **this API repository** with a meaningful summary of all the commits made during the workflow. Notify the developer that the workflow was completed and provide a link to the PR.

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

- **External prerequisites**
  - Work in other repositories (MongoDB dictionary changes, `make schemas`, SPA UI) is **not** orchestrated from this folder.
  - Record external preconditions under **Context** or set **Status** to `Blocked` until a human confirms they are satisfied.
  - **Depends On** references only tasks in **this repo's** `tasks/` folder.

### Sample task file

For a complete example of a well‑formed `Run as needed` task, see:

- `AS_NEEDED.T998.example_update_openapi.md`

## Task execution workflow

The steps below apply to the agent that executes a task.

1. **Review the current tasks**
   - Each task is a markdown file in this repo's `tasks/` folder (e.g. `PENDING.L010.update_profile_openapi.md`).
   - For each task, read the entire file before starting work.

2. **Change control for each task**
   For every task, the agent should:
   - **Review Context and Goals**: Read all referenced input/context files.
   - **Plan changes**: Summarize the planned approach in the **Execution Notes** section of the task file.
   - **Implement changes**: Update code, configuration, docs, etc., as required — only files listed under **Outputs**.
   - **Testing**: Follow the instructions in the task file's **Testing Expectations** section.

3. **Completion and documentation**
   - After successful testing, update **Execution Notes** with summary and test results.
   - Set **Status** to `Shipped` and rename the file to `SHIPPED.*`.
   - If follow‑ups are discovered, add them as new `PENDING.*` tasks instead of over‑expanding the current one.
