# F365 – Update API GitHub Actions for AWS-free validation and GHCR publishing

**Status**: Pending

**Type**: Feature

**Depends On**: F364

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — update api github actions for aws-free validation and ghcr publishing.

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
- `.github/workflows/docker-push.yml`

Source issue is authoritative for this migration. The agreed migration supersedes old CodeArtifact-auth prerequisites only in the paths explicitly migrated by these tasks; do not rewrite unrelated framework rules.

## Goals

- Remove configure-aws-credentials, CodeArtifact token/index steps, AWS_ROLE_ARN_READ, CODEARTIFACT_* env and unnecessary id-token permissions from docker-push.yml. Preserve push-to-main GHCR publishing with packages: write, contents: read and existing platforms.
- Add separate pull_request-to-main validation using committed locks and AWS-free container builds/tests, with no registry push and no write tokens on untrusted fork PRs. Do not add PR triggers to the publishing workflow.
- Record GitHub workflow evidence after the branch is separately pushed; document permissions and remove outdated OIDC docs where present. No live AWS calls or credentials required.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- Review YAML, triggers, permissions and Docker inputs; ensure no undeclared build-arg/index remains. Run lint/unit/build/container gates locally during implementation. CI evidence is post-push; do not push merely to satisfy this task without authorization.

## Outputs

- `.github/workflows/docker-push.yml`
- `.github/workflows/ci.yml`
- `docs/aws-exit.md`

Only these implementation files may change. The orchestrator may also update/rename this task record under the established lifecycle.

## Execution boundary

This is a reviewable plan, not an execution record. Execute only this task's listed outputs when orchestration is separately authorized. Do not touch excluded MongoDB/Runbook utility repos, publish packages/tags, mutate issue/project state, or delete/provision AWS resources as a side effect. Future workflow publication happens only through the reviewed maintainer release path.

Where a task requires an unpublished release, an undecided production contract, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Production identity/hosting decisions and cutover readiness: https://github.com/mentor-forge/mentorhub/issues/80. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Execution Notes

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
