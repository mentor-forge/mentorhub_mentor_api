# API Task Automation Framework - Orchestration

This folder contains coding tasks that an orchestration agent can execute, based on the context and instructions in each task file. All of these tasks will only make changes in this API repo. The agent will first help to plan tasks, and then orchestrate execution of all Pending Tasks to implement a Feature.

**Static Framework Guidelines**: `tasks/_ORCHESTRATE.md` and `tasks/_PLANNING.md` are static, standalone framework guidelines. Agents must NEVER modify `tasks/_ORCHESTRATE.md` or `tasks/_PLANNING.md` during task planning or orchestration (no adding run-specific checklists, notes, or execution logs to these files).

## Orchestration model: Feature Workflow

Before starting the workflow, check to make sure you are not on the main branch, and that you can push on the branch you are on. If you fail this test, pause and ask the developer how you should proceed, and then select or create a branch as instructed before starting the first task.

Now orchestrate all Pending Tasks as outlined below. Use an **orchestration agent** that spawns a **fresh agent per task**:

1. **Orchestrator** discovers all tasks, respects dependencies, and determines execution order.
   - **Task Selection**: Select only `PENDING.*` tasks.
   - **Execution order**: Review all PENDING tasks and order dependencies first.
   - Do not schedule **concurrent** agents to avoid testing collisions.
2. **For each task**, the orchestrator selects the least expensive model that can provide good results. Many tasks will not need high reasoning models. Prefer GROK and default models. Then, launch a new agent with:
   - The task file path
   - Any outputs from prior tasks (e.g. "L010 complete; Profile schema updated in openapi.yaml")
3. **Sub-agent** executes only that task: read context, implement, test, update task notes.
4. **Orchestrator Confirmation**: The orchestrator should repeat drop/config testing as outlined in the task.
5. **Commit Changes**: The orchestrator is responsible for a commit, with a meaningful message, and a push.
6. **Mark Shipped** by updating the task status, and renaming the task file like `SHIPPED.T010_update_profile_data.md`.
7. **Orchestrator** after the commit, moves to the next task.

**Task Failure Case**: In the event a task fails, execution should halt and the developer should receive a summary of the current state and error condition that caused the failure.

**Mandatory Pre-PR QA Gate**:
Before opening a Pull Request, the orchestration agent MUST execute the full end-to-end integration and packaging gate:
```bash
pipenv run container && pipenv run api && pipenv run e2e
```
All E2E tests must pass 100%. If any test fails, pause and resolve the failure before proceeding.

**All Tasks Complete**: Once all tasks and the mandatory Pre-PR QA Gate have successfully completed, the orchestration agent should create a Pull Request in **this API repository** with a meaningful summary of all the commits made during the workflow. Notify the developer that the workflow was completed and provide a link to the PR.

## Implementation Details
- **Recommended filename pattern**:
  - `STATUS.LNNN.short_task_name.md`
  - Examples:
    - `AS_NEEDED.T998.example_update_openapi.md`
    - `PENDING.L010.update_profile_openapi.md`
    - `RUNNING.L020.add_profile_field_tests.md`
    - `SHIPPED.L010.update_profile_openapi.md`

- **External prerequisites**
  - Work in other repositories (MongoDB dictionary changes, SPA UI) is **not** orchestrated from this folder.
  - Record external preconditions under **Context** or set **Status** to `Blocked` until a human confirms they are satisfied.
  - **Depends On** references only tasks in **this repo's** `tasks/` folder.

## Task execution workflow

The steps below apply to the agent that executes a task.

1. **Review the current tasks**
   - Each task is a markdown file in this repo's `tasks/` folder (e.g. `PENDING.L010.update_profile_openapi.md`).
   - For each task, read the entire file before starting work.

2. **Change control for each task**
   For every task, the agent should:
   - **Review Context and Goals**: Read all referenced input/context files.
   - **Plan changes**: Summarize the planned approach in the **Execution Notes** section of the task file.
   - **Implement changes**: Update configuration, docs, etc., as required — only files listed under **Outputs**.
   - **Testing**: Follow the instructions in the task file's **Testing Expectations** section.

3. **Completion and documentation**
   - After successful testing, update **Execution Notes** with summary and test results.
   - The sub agent does not need to commit changes, the orchestrating agent handles that.
