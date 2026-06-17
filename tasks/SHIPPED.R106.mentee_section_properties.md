# R106 – Mentee section and Properties hub

**Status**: Shipped  
**Task Type**: Feature  

This API repo implements `GET /api/profile/{id}/properties`.

For the full cross-repo contract (SPA routes, curl examples, response shape, testing), see:

**[mentorhub/Tasks/SHIPPED.R106.mentee_section_properties.md](../../mentorhub/Tasks/SHIPPED.R106.mentee_section_properties.md)**

## API-specific files

| File | Change |
|------|--------|
| `src/services/profile_service.py` | `get_profile_properties`, helpers |
| `src/routes/profile_routes.py` | Route registered **before** `GET /api/profile/<id>` |
| `docs/openapi.yaml` | Path + `ProfilePropertiesResponse` schemas |
| `test/services/test_profile_service.py` | Service unit tests |
| `test/routes/test_profile_routes.py` | Route unit test |
| `test/e2e/test_profile.py` | E2E smoke test |
| `README.md` | Profile domain table + curl examples |

## Quick test

```bash
pipenv run test
pipenv run api && pipenv run e2e && pipenv run down
```
