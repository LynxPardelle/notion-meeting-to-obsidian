# Testing

## Backend

Backend tests use Pytest.

Run:

```powershell
cd backend
python -m pytest
```

Current coverage areas:

- API behavior and CORS.
- Notion-to-Markdown conversion.
- Editable meeting card parsing/saving.
- Notion property metadata.
- Notion API error handling.
- Sync state persistence.
- Sync behavior, hierarchy, stale cleanup, renames, local card preservation, and delta file updates.

## Frontend

The repo currently verifies frontend production build with:

```powershell
cd frontend
npm run build
```

`npm test` exists in `frontend/package.json`, but no dedicated Angular spec files are visible in the current source tree.

## Dependency Checks

Useful checks:

```powershell
cd frontend
npm audit --omit=dev
```

```powershell
cd backend
python -m pip check
```

## Docker Verification

After Docker rebuild:

```powershell
docker compose ps
Invoke-WebRequest -Uri http://127.0.0.1:47863/api/health -UseBasicParsing
```

## Evidence

- `backend/pyproject.toml`
- `backend/tests/test_api.py`
- `backend/tests/test_converter.py`
- `backend/tests/test_meeting_card.py`
- `backend/tests/test_metadata.py`
- `backend/tests/test_notion.py`
- `backend/tests/test_state_writer.py`
- `backend/tests/test_sync.py`
- `frontend/package.json`
