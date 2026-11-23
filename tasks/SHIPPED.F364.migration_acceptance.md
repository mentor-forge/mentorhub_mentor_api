# F364 Verify Mentor API locally and document rollback

- Status: Shipped
- Type: Feature
- Depends On: F363_github_actions
- Description: Verify Mentor API locally and document rollback.

## Context

- https://github.com/mentor-forge/mentorhub_mentor_api/issues/43
- `README.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub_api_utils/README.md`
- Use the distribution policy in the originating issue while the shared standards are being updated.

## Goals

- Audit executable AWS dependencies versus placeholders and document the AWS-free developer flow and rollback to the previous reviewed dependency and image.

## Testing Expectations

- Run packaged API against local backing services. Verify Mentor persona auth and representative mentee, plan and encounter routes against the existing OpenAPI contract.

## Acceptance Criteria

- Record the commands, results, and any follow-up evidence needed in the pull request. Preserve application contracts and existing local behavior.

## Outputs

- `README.md`
- `test/e2e/test_profile.py`

## Execution Notes

- Audited the dependency manifests, active source, scripts, Dockerfile, and
  workflows. The current runtime uses MongoDB and OIDC JWT claims. The historical
  Cognito subject field remains in OpenAPI for data compatibility. The approved
  distribution policy in the migration issue supersedes the historical
  CodeArtifact instructions in the static planning guide.
- The packaged test harness used the locally built Mentor API image, isolated
  Docker networking and MongoDB seeded by the existing schema service. It
  exercised the application using the existing HTTP test suite without bringing
  down shared Developer Edition services.
- The default admin fixture has no assigned mentees. The dashboard list and
  properties checks now exercise a seeded mentor with assigned profiles. The
  composite check selects a real profile from that dashboard and uses its
  original privileged authorization. The mentor-only composite request returned
  404 on the seeded mentee during validation. Investigate that visibility behavior
  independently of the packaging migration.
- Packaged E2E finished with all 53 tests passing. Docs, OpenAPI, metrics and
  authenticated config returned 200, and unauthenticated resource access
  returned 401. PyJWT reported the existing Developer Edition fixture key
  length warning. Hosted CI verification follows pull request creation.
