#!/usr/bin/env sh
# Regenerate Pipfile.lock against CodeArtifact (run `mh` first, or auto SSO login).
set -e

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

# shellcheck disable=SC1091
. "${HOME}/.mentorhub/codeartifact-pypi-auth.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")/../../mentorhub/DeveloperEdition/scripts" && pwd)/codeartifact-pypi-auth.sh"

codeartifact_load_env
codeartifact_ensure_sso
MIRROR=$(codeartifact_pypi_mirror_url)

pipenv lock --pypi-mirror "${MIRROR}"
