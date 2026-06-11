#!/usr/bin/env sh
# Install dependencies from Pipfile.lock using CodeArtifact (run `mh` first, or auto SSO login).
set -e

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

# shellcheck disable=SC1091
. "${HOME}/.mentorhub/codeartifact-pypi-auth.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")/../../mentorhub/DeveloperEdition/scripts" && pwd)/codeartifact-pypi-auth.sh"

codeartifact_load_env
codeartifact_ensure_sso
MIRROR=$(codeartifact_pypi_mirror_url)

if ! pipenv --venv >/dev/null 2>&1; then
  pipenv --python 3.12
fi

pipenv requirements --dev | grep -v '^-i ' > .pipenv-requirements.txt
pipenv run pip install --index-url "${MIRROR}" -r .pipenv-requirements.txt
rm -f .pipenv-requirements.txt
