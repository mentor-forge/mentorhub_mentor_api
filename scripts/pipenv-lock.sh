#!/usr/bin/env sh
# Regenerate Pipfile.lock against CodeArtifact (run `mh` first, or use AWS SSO profile).
set -e

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

domain="${CODEARTIFACT_DOMAIN:-mentor-forge}"
owner="${AWS_SHARED_SERVICES_ACCOUNT_ID:-560167829275}"
repo="${CODEARTIFACT_PYPI_REPO:-mentorhub-pypi}"
region="${AWS_REGION:-us-east-1}"

export AWS_PROFILE="${MH_AWS_PROFILE_SHARED:-mentorhub-shared}"

TOKEN=$(aws codeartifact get-authorization-token \
  --domain "${domain}" \
  --domain-owner "${owner}" \
  --region "${region}" \
  --query authorizationToken --output text)

END=$(aws codeartifact get-repository-endpoint \
  --domain "${domain}" \
  --domain-owner "${owner}" \
  --repository "${repo}" \
  --format pypi \
  --region "${region}" \
  --query repositoryEndpoint --output text)

HOST="${END#https://}"
MIRROR="https://aws:${TOKEN}@${HOST}simple/"

pipenv lock --pypi-mirror "${MIRROR}"
