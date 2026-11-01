# F362 – Audit AWS coupling and release prerequisites

**Status**: Pending

**Type**: Feature

**Depends On**: none

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — audit aws coupling and release prerequisites.

**Issue**: [I-RA01](https://github.com/mentor-forge/mentorhub_mentor_api/issues/43)

## Path anchoring

All output paths are relative to this repository root. Sibling references are read-only context permitted by the repo planning guide.

## Context

- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/sre_standards.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/flask_utils/token.py`
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`

Source issue is authoritative for this migration. The agreed migration supersedes old CodeArtifact-auth prerequisites only in the paths explicitly migrated by these tasks; do not rewrite unrelated framework rules.

## Goals

- Inventory this repo's CodeArtifact install/lock wrappers, Dockerfile, GitHub Actions, runtime env and AWS-specific calls. Document exact touched paths, source/pin policy and rollback; distinguish historical Cognito data from active service dependency.
- Record package cutover prerequisite: actual published public API utils wheel and hash from I-UA01. The planned 1.0.5 candidate is not an available release until verified. Inspect current pin and reconcile existing unfinished pin tasks without executing unrelated tasks.
- Audit Token claims and helper signatures in the shared library; preserve MongoIO-only database access and existing JWT validation/RBAC. No schema or OpenAPI behavior changes are planned by dependency delivery migration.
- Current tracked runtime source search found no direct Cognito/AWS SDK calls outside build/auth wrappers; verify and record the result rather than adding a replacement adapter unnecessarily.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- Review tracked source/config/workflow references and existing task coverage; do not start services or change runtime in this audit.

## Outputs

- `docs/aws-exit.md`

Only these implementation files may change. The orchestrator may also update/rename this task record under the established lifecycle.

## Execution boundary

This is a reviewable plan, not an execution record. Execute only this task's listed outputs when orchestration is separately authorized. Do not touch excluded MongoDB/Runbook utility repos, publish packages/tags, mutate issue/project state, or delete/provision AWS resources as a side effect. Future workflow publication happens only through the reviewed maintainer release path.

Where a task requires an unpublished release, an undecided production contract, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Production identity/hosting decisions and cutover readiness: https://github.com/mentor-forge/mentorhub/issues/80. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Execution Notes

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
