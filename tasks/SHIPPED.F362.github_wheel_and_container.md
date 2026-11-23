# F362 Install the public API utils wheel and build without AWS

- Status: Shipped
- Type: Feature
- Depends On: none
- Description: Install the public API utils wheel and build without AWS.

## Context

- https://github.com/mentor-forge/mentorhub_mentor_api/issues/43
- `README.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub_api_utils/README.md`
- Use the distribution policy in the originating issue while the shared standards are being updated.

## Goals

- Verify the supported published wheel used by the Mentee API migration. Pin its exact versioned HTTPS URL in Pipfile, use public PyPI for other dependencies, regenerate Pipfile.lock with hashes, and remove CodeArtifact inputs from the install, lock, and Docker build paths.

## Testing Expectations

- Run clean locked install and image build without AWS credentials. Verify Mentor Hub Config/auth imports and run unit tests.

## Acceptance Criteria

- Record the commands, results, and any follow-up evidence needed in the pull request. Preserve application contracts and existing local behavior.

## Outputs

- `Pipfile` and `Pipfile.lock`
- `Dockerfile` and `scripts/docker-build.sh`
- `scripts/pipenv-install.sh` and `scripts/pipenv-lock.sh` (obsolete wrappers)
- `README.md`

## Execution Notes

Use the published API Utils 1.0.5 wheel and SHA-256 from the validated Mentee
API migration. Regenerate the lock from public sources and use the hashed
runtime export in the container. Preserve the Mentor API image name,
entrypoint, and port.

- Regenerated and verified the lock with public PyPI and the exact API Utils
  wheel. A fresh Python 3.12 environment installed the committed lock without
  AWS credentials. Config and auth imports resolved from API Utils 1.0.5.
- `pipenv run test`: 192 passed. The 53 E2E tests were deselected by the
  unit-test command.
- Built the ARM64 image without AWS credentials. The runtime image imported
  Config and auth helpers, and its installed metadata reported the expected
  wheel URL and SHA-256. Image history had no AWS index wiring. Port 8391,
  the existing entrypoint, and the default GHCR image name were preserved.
- The existing Docker shell-form CMD warning remains. Packaged E2E and hosted
  CI are covered by the remaining tasks.
