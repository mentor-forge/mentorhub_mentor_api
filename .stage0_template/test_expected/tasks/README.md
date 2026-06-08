This folder contains coding tasks that a long‑running agent session can execute one at a time, based on the context and instructions in each task file.

### Task execution workflow

1. **Review all tasks**
   - Each task is a markdown file in this folder (e.g., `T001_add_healthcheck.md`).
   - The agent should first **list all tasks**, then determine the **execution order** (see **Task ordering** below).
   - For each task, read the entire file before starting work.

2. **Execute one task at a time**
   - Pick the **next eligible task** (not completed, not "Run as needed", and in order).
   - Follow the **Task lifecycle** (analysis → implementation → testing → completion notes → change control).
   - Do not start another task until the current one is finished or explicitly deferred.

3. **Change control for each task**
   For every task, the agent should:
   - **Review context**: Read all referenced input/context files.
   - **Plan changes**: Summarize the planned approach in the notes section of the task file.
   - **Implement changes**: Update code, configuration, docs, etc., as required.
   - **Unit tests (Pipenv)**:
     - Add or update unit tests when behavior changes or new behavior is introduced.
     - Run unit tests with:
       - `pipenv run test`
     - Ensure `pipenv run test` completes successfully.
   - **Container build (Pipenv)**:
     - Build the container image with:
       - `pipenv run container`
   - **End‑to‑end (e2e) tests (Pipenv)**:
     - Start the API/service:
       - `pipenv run api`
     - Run e2e tests:
       - `pipenv run e2e`
     - Tear down services:
       - `pipenv run down`
     - Ensure this full sequence completes successfully.
   - **Commit gating**:
     - Only create a commit once `pipenv run test`, `pipenv run container`, and the `pipenv run api` / `pipenv run e2e` / `pipenv run down` flow are in a healthy state.
     - Keep commits scoped to the current task.

4. **Completion and documentation**
   - Update the task file’s **status** and **implementation notes**.
   - If follow‑ups are discovered, add them as new tasks instead of over‑expanding the current one.

### Task ordering

- **Primary mechanism**: A task’s filename should start with a sortable prefix (e.g., `T001_`, `T002_`, `T010_`).
- **Execution order**:
  - Sort all task files by filename.
  - Skip tasks explicitly marked as **Run as needed** (see below).
  - Skip tasks with status **Completed**.
  - Process remaining tasks in sorted order.
- **Manual overrides**:
  - If a task must run earlier/later, note this in the task’s **Dependencies / Ordering** section; the agent should respect these dependencies when building its execution plan.

### Task status, categories, and filenames

Each task file should declare status and type **inside the file**, and also encode the status in the **filename prefix** so tasks are visually grouped in the IDE.

- **Lifecycle statuses (in‑file)**:
  - `Pending`: Not yet started.
  - `Running`: Work is currently being done in the active session.
  - `Blocked`: Waiting on some external dependency or decision.
  - `Shipped`: Implemented, tested, and merged/committed as per the change control process.
  - `Run as needed`: Not part of the main long‑running sequence; to be run manually or opportunistically.

- **Filename status prefixes (for grouping)**:
  - `AS_NEEDED.` – Tasks that should **not** be part of the main long‑running sequence.
  - `BLOCKED.` – Tasks currently blocked.
  - `PENDING.` – Tasks that are ready to be picked up when their turn comes.
  - `RUNNING.` – (Optional) Tasks currently being executed in this session.
  - `SHIPPED.` – Tasks that are fully implemented and completed.

- **Recommended filename pattern**:
  - `STATUS.RNNN.short_task_name.md`
  - Examples:
    - `AS_NEEDED.R900.example_add_healthcheck.md`
    - `PENDING.R010.add_healthcheck_endpoint.md`
    - `RUNNING.R050.implement_bulk_import.md`
    - `SHIPPED.R100.configure_ci_pipeline.md`

- **Task type** (in‑file, optional but helpful):
  - `Feature`, `Refactor`, `Bugfix`, `Chore`, `Docs`, etc.

### Sample task file

For a complete example of a well‑formed `Run as needed` task (including context files, testing expectations, change control checklist, and implementation notes), see:

- `AS_NEEDED.sample.md`

### Marking a task as completed or "Run as needed"

- **Completed task**:
  - Update `Status` to `Completed`.
  - Fill in the **Implementation notes** and **Testing results** while the work and test commands are still fresh.
  - Ensure all items in the **Change control checklist** are checked or explicitly commented if intentionally skipped (with rationale).
  - **Only after the notes are updated and the checklist is satisfied**, create a scoped commit referencing this task ID.

- **Run as needed task**:
  - The long‑running agent should **not** include these tasks in its default sequential run; they are to be invoked manually when appropriate.

With this structure, a long‑running agent can:
- Discover tasks by listing markdown files in this folder.
- Determine order and eligibility based on filenames, `Status`, and `Run Mode`.
- Apply a consistent change control process (analysis, testing, packaging, commit) for each task.
