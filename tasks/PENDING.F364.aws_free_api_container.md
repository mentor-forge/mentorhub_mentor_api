# F364 – Remove AWS auth from API Docker builds

**Status**: Pending

**Type**: Feature

**Depends On**: F363

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — remove aws auth from api docker builds.

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
- `Dockerfile`
- `scripts/docker-build.sh`

Source issue is authoritative for this migration. The agreed migration supersedes old CodeArtifact-auth prerequisites only in the paths explicitly migrated by these tasks; do not rewrite unrelated framework rules.

## Goals

- Remove ARG PIP_INDEX_URL, CodeArtifact index/token construction and shared home auth helper dependency from Dockerfile and docker-build.sh. Install public transitives and exact wheel from the committed lock/exported direct URLs, preserving hashes where supported.
- Preserve multi-stage build, compile step, runtime port/entrypoint/docs and GHCR image identity. Remove only now-obsolete AWS auth wiring; do not introduce GitHub tokens for public wheel downloads.
- Ensure build failures remain actionable and no credentials are stored in layers, arguments or logs. Keep pipenv run container working without AWS CLI or mh login.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- Run pipenv run container without AWS environment/auth helpers and inspect installed wheel origin/version in the image. Run pipenv run api then pipenv run e2e with existing local JWT settings; verify /docs, config, metrics and negative authorization cases. Check locked direct URL is not lost by requirements export.

## Outputs

- `Dockerfile`
- `scripts/docker-build.sh`
- `docs/aws-exit.md`

Only these implementation files may change. The orchestrator may also update/rename this task record under the established lifecycle.

## Execution boundary

This is a reviewable plan, not an execution record. Execute only this task's listed outputs when orchestration is separately authorized. Do not touch excluded MongoDB/Runbook utility repos, publish packages/tags, mutate issue/project state, or delete/provision AWS resources as a side effect. Future workflow publication happens only through the reviewed maintainer release path.

Where a task requires an unpublished release, an undecided production contract, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Production identity/hosting decisions and cutover readiness: https://github.com/mentor-forge/mentorhub/issues/80. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Execution Notes

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
