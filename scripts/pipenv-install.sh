#!/usr/bin/env sh
# Install dependencies from Pipfile.lock using CodeArtifact (run `mh` first).
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

if ! pipenv --venv >/dev/null 2>&1; then
  pipenv --python 3.12
fi

pipenv requirements --dev | grep -v '^-i ' > .pipenv-requirements.txt
pipenv run pip install --index-url "${MIRROR}" -r .pipenv-requirements.txt
rm -f .pipenv-requirements.txt
