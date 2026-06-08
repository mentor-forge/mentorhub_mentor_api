# Template Flask MongoDB API

This is a Flask + MongoDB API template that demonstrates the {{info.name}} architecture patterns with three domain types: Control (full CRUD), Create (create and read), and Consume (read-only). 

## Prerequisites
- {{info.name}} [Developers Edition]({{org.git_host.name}}/{{org.git_org.name}}/{{info.slug}}/blob/main/DeveloperEdition/README.md)
- Developer [API Standard Prerequisites]({{org.git_host.name}}/{{org.git_org.name}}/{{info.slug}}/blob/main/DeveloperEdition/standards/api_standards.md)

## Developer Commands

```bash
## Install dependencies (including dev: pytest, requests for E2E)
pipenv install --dev

# start backing db container 
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests 
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8184
pipenv run dev

## run E2E tests (assumes running API at localhost:8184)
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

List endpoints (`GET /api/control`, `GET /api/create`, `GET /api/consume`) use server-side infinite scroll via `api_utils.mongo_utils.execute_infinite_scroll_query`. They support `?name=`, `?after_id=`, `?limit=`, `?sort_by=`, and `?order=` and return `{ items, limit, has_more, next_cursor }`. Invalid params return `400 Bad Request`.

### Control Domain (Full CRUD)
- `POST /api/control` - Create a new control document
- `GET /api/control` - List controls (infinite scroll; `?name=`, `?after_id=`, `?limit=`, `?sort_by=`, `?order=`)
- `GET /api/control/{id}` - Get a specific control document
- `PATCH /api/control/{id}` - Update a control document

### Create Domain (Create + Read)
- `POST /api/create` - Create a new create document
- `GET /api/create` - List creates (infinite scroll; same query params)
- `GET /api/create/{id}` - Get a specific create document

### Consume Domain (Read-only)
- `GET /api/consume` - List consumes (infinite scroll; same query params)
- `GET /api/consume/{id}` - Get a specific consume document

### Common Endpoints
- `GET /docs` - API Explorer (OpenAPI/Swagger documentation)
- `GET /api/config` - Configuration endpoint
- `GET /metrics` - Prometheus metrics

See the [project swagger](./docs/openapi.yaml) for detailed endpoint information.

Local JWTs come from the Developer Edition welcome / IdP flow, not from this API. For automated E2E,
use the static token in `test/e2e/e2e_auth.py` (`E2E_ACCESS_TOKEN`) with `pipenv run dev` (same default
`JWT_SECRET` as in `Pipfile`).

### Simple Curl Commands:
```bash
# Bearer token: export from welcome flow, or: export TOKEN="$(python -c 'from test.e2e.e2e_auth import E2E_ACCESS_TOKEN; print(E2E_ACCESS_TOKEN)')"

# Control endpoints
curl http://localhost:8184/api/control \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8184/api/control?name=test \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8184/api/control \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"my-control","description":"Test control","status":"active"}'

curl -X PATCH http://localhost:8184/api/control/{id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status":"archived"}'

# Create endpoints
curl -X POST http://localhost:8184/api/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"my-create","status":"active"}'

curl http://localhost:8184/api/create \
  -H "Authorization: Bearer $TOKEN"

# Consume endpoints
curl http://localhost:8184/api/consume \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8184/api/consume?name=test \
  -H "Authorization: Bearer $TOKEN"
```

## RBAC
All services implement a placeholder RBAC pattern for future authorization implementation:
- **Control Service**: Requires valid authentication token (RBAC placeholder for future implementation)
- **Create Service**: Requires valid authentication token (RBAC placeholder for future implementation)
- **Consume Service**: Requires valid authentication token (RBAC placeholder for future implementation)

The RBAC pattern is implemented as `_check_permission()` methods that currently pass through, allowing easy future implementation of role-based access control.
