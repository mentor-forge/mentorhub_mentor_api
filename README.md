# Mentor Hub — Mentor API

## Prerequisites
- Mentor Hub [Developers Edition](https://github.com/mentor-forge/mentorhub/blob/main/CONTRIBUTING.md)
- Developer [API Standard Prerequisites](https://github.com/mentor-forge/mentorhub/blob/main/DeveloperEdition/standards/api_standards.md)

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
  - `routes/` - HTTP request/response handlers
  - `services/` - Business logic and RBAC

- `test/` - Test suite with matching directory structure:
  - `routes/` - Route unit tests
  - `services/` - Service unit tests
  - `e2e/` - End-to-end tests flagged with `@pytest.mark.e2e`

## API Endpoints

see the [Open API Specifications](./docs/openapi.yaml) for details on the API

For E2E, mint a Bearer token via `test/e2e/e2e_auth.py` (`get_auth_token()`) with `pipenv run dev` (matching `JWT_SECRET`).

### Profile domain (mentor dashboard + mentee detail)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/profile` | Mentor dashboard — mentee cards for the logged-in mentor |
| `GET` | `/api/profile/{profileId}` | Single mentee Profile document (read-only) |
| `GET` | `/api/profile/{profileId}/properties` | Aggregated Properties hub (journey, resources, mentors, celebrations) |

All Profile routes require the **`mentor`** role. Flask serves lowercase paths (`/api/profile`); OpenAPI documents the same contract.

**SPA routes (mentorhub_mentor_spa):**

| SPA route | API used |
|-----------|----------|
| `/profiles` | `GET /api/profile` |
| `/profiles/:id` | `GET /api/profile/:id`, `GET /api/encounter` (filter by `mentee_id`) |
| `/profiles/:id/properties` | `GET /api/profile/:id/properties` |

### Simple Curl Commands:
```bash
# Bearer token for local dev (same JWT settings as pipenv run dev / e2e):
export TOKEN="$(PYTHONPATH=. pipenv run python -c 'from test.e2e.e2e_auth import get_auth_token; print(get_auth_token())')"

# Get the API Configuration
curl http://localhost:8391/api/config \
  -H "Authorization: Bearer $TOKEN"

# Mentor dashboard (mentee cards)
curl http://localhost:8391/api/profile \
  -H "Authorization: Bearer $TOKEN"

# Single mentee profile (replace MENTEE_ID)
curl http://localhost:8391/api/profile/MENTEE_ID \
  -H "Authorization: Bearer $TOKEN"

# Mentee Properties hub (replace MENTEE_ID)
curl http://localhost:8391/api/profile/MENTEE_ID/properties \
  -H "Authorization: Bearer $TOKEN"

```