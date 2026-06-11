#!/usr/bin/env sh
# Local Docker build with CodeArtifact PyPI auth (run `mh` first, or set AWS SSO profile).
set -e

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
PIP_INDEX_URL="https://aws:${TOKEN}@${HOST}simple/"

docker build --build-arg "PIP_INDEX_URL=${PIP_INDEX_URL}" \
  -t ghcr.io/mentor-forge/mentorhub_mentor_api:latest .
