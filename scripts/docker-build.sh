#!/usr/bin/env sh
# Local Docker build with CodeArtifact PyPI auth (run `mh` first, or auto SSO login).
set -e

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

# shellcheck disable=SC1091
. "${HOME}/.mentorhub/codeartifact-pypi-auth.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")/../../mentorhub/DeveloperEdition/scripts" && pwd)/codeartifact-pypi-auth.sh"

codeartifact_load_env
codeartifact_ensure_sso
PIP_INDEX_URL=$(codeartifact_pypi_mirror_url)

docker build --build-arg "PIP_INDEX_URL=${PIP_INDEX_URL}" \
  -t ghcr.io/mentor-forge/mentorhub_mentor_api:latest .
