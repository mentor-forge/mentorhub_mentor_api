# Mentor Hub — Mentor API

## Prerequisites
- Mentor Hub [Developers Edition](https://github.com/mentor-forge/mentorhub/blob/main/CONTRIBUTING.md)
- Developer [API Standard Prerequisites](https://github.com/mentor-forge/mentorhub/blob/main/DeveloperEdition/standards/api_standards.md)
- Dependency: `api-utils==1.0.0` (pinned in `Pipfile` via CodeArtifact)

## Architecture & Subclassing

- **Services (`src/services/`)**: Subclass the shared domain services from `api_utils.services` (e.g. `ResourceService`, `PathService`, `PlanService`, `EncounterService`, `MenteeService`, `EventService`, `JourneyService`, `ProfileService`). Subclasses implement mentor-local write CRUD (POST/PATCH), Mentor Dashboard aggregation, composite views, and inbound RBAC checks (`ROLE_MENTOR` / `ROLE_ADMIN`).
- **Routes (`src/routes/`)**: Mount shared consume GET endpoints using factory functions from `api_utils.routes.shared_get_routes` passing the local service subclasses. Local write operations (POST, PATCH) and specialized endpoints (e.g. Properties hub) are mounted on the returned blueprints.
- **List GET Contract**: List GET endpoints return a plain JSON array (status `200`). Pagination is controlled via `offset` and `size` request headers (defaulting to offset 0, size 20), without `X-Pagination-*` response headers.

## Developer Commands

```bash
## Install dependencies (run `mh` first for CodeArtifact auth)
pipenv run install

# start backing db container 
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests 
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8391
pipenv run dev

## run E2E tests (assumes running API at localhost:8391)
pipenv run e2e

## run tests with coverage report
pipenv run coverage

## build application (pre-compiles Python code)
pipenv run build

## build container 
pipenv run container

## Run the backing database and api containers
pipenv run api

## Run the full microservice (db+api+spa)
pipenv run service

## format code
pipenv run format

## lint code
pipenv run lint
```

## Project Structure

- `src/` - Main package containing:
  - `server.py` - API entrypoint
  - `routes/` - HTTP request/response handlers (wired via shared GET factories and local blueprints)
  - `services/` - Business logic and RBAC (subclassing `api_utils.services`)

- `test/` - Test suite with matching directory structure:
  - `routes/` - Route unit tests
  - `services/` - Service unit tests
  - `e2e/` - End-to-end tests flagged with `@pytest.mark.e2e`

## API Endpoints

see the [Open API Specifications](./docs/openapi.yaml) for details on the API

For E2E, mint a Bearer token via `test/e2e/e2e_auth.py` (`get_auth_token()`) with `pipenv run dev` (matching `JWT_SECRET`).

### Simple Curl Commands:
```bash
# Bearer token for local dev (same JWT settings as pipenv run dev / e2e):
export TOKEN="$(PYTHONPATH=. pipenv run python -c 'from test.e2e.e2e_auth import get_auth_token; print(get_auth_token())')"

# Get the API Configuration
curl http://localhost:8391/api/config \
  -H "Authorization: Bearer $TOKEN"

```