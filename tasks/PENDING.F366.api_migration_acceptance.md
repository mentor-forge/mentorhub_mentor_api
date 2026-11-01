# F366 – Finalize API migration documentation and runtime acceptance

**Status**: Pending

**Type**: Feature

**Depends On**: F365

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — finalize api migration documentation and runtime acceptance.

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

- Update active README and only dependency instructions in tasks/_PLANNING.md to match pipenv run install, exact wheel URL/lock policy and AWS-free Docker/CI. Record external upstream pin readiness and rollback.
- Verify JWT issuer/audience/signature and service endpoints are configurable for the approved non-AWS environment; preserve existing API behavior. If inventory found no runtime AWS calls, record that evidence rather than implement unnecessary provider-specific code.
- Record complete clean-install, test, Docker and CI acceptance; tests must use the selected library version and current display_name/tenant claims. Only this repo is modified. Do not execute other pending features or change issue/project state.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- pipenv run install, pipenv run test, pipenv run lint, pipenv run build and pipenv run container && pipenv run api && pipenv run e2e. Verify least-privileged/invalid tokens still fail and positive flows work without AWS. Runtime cutover depends on approved I-WE01 identity/hosting readiness; record it explicitly if not available.

## Outputs

- `README.md`
- `tasks/_PLANNING.md`
- `docs/aws-exit.md`

Only these implementation files may change. The orchestrator may also update/rename this task record under the established lifecycle.

## Execution boundary

This is a reviewable plan, not an execution record. Execute only this task's listed outputs when orchestration is separately authorized. Do not touch excluded MongoDB/Runbook utility repos, publish packages/tags, mutate issue/project state, or delete/provision AWS resources as a side effect. Future workflow publication happens only through the reviewed maintainer release path.

Where a task requires an unpublished release, an undecided production contract, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Production identity/hosting decisions and cutover readiness: https://github.com/mentor-forge/mentorhub/issues/80. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Execution Notes

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
