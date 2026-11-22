# F363 Move Mentor API CI off AWS

- Status: Shipped
- Type: Feature
- Depends On: F362_github_wheel_and_container
- Description: Move Mentor API CI off AWS.

## Context

- https://github.com/mentor-forge/mentorhub_mentor_api/issues/43
- `README.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub_api_utils/README.md`
- Use the distribution policy in the originating issue while the shared standards are being updated.

## Goals

- Update workflows to use the locked public dependencies, eliminate obsolete AWS auth and permissions, and preserve GHCR output, platforms, triggers and test gates.

## Testing Expectations

- Run workflow validation and verify hosted PR checks and image build.

## Acceptance Criteria

- Record the commands, results, and any follow-up evidence needed in the pull request. Preserve application contracts and existing local behavior.

## Outputs

- `.github/workflows/ci.yml`
- `.github/workflows/docker-push.yml`

## Execution Notes

- Adapted the Mentee API workflow pattern. Main-targeted pull requests verify the lock, install locked development dependencies, run lint and unit tests, compile the source, and build a validation image. Main pushes retain AMD64 and ARM64 GHCR publishing with package write access.
- Removed AWS token acquisition, OIDC permissions, and the build-time private index argument. Both workflows disable checkout credential persistence.
- Parsed the YAML with `yq` and checked the branch triggers, permissions, target architectures, push flag, and image tag. A workflow scan found no AWS, CodeArtifact, or private-index references.
- `pipenv verify`, `pipenv sync --dev`, `pipenv run lint`, `pipenv run test`, `pipenv run build`, and the CI image build passed locally. The unit gate passed 192 tests with 53 end-to-end tests deselected. `git diff --check` passed.
- Verify hosted pull request CI after opening the PR. The publish workflow starts on main push after merge.
