# Stack

## Runtime

- Backend: Python package requiring Python `>=3.11`.
- Backend framework: FastAPI with Uvicorn.
- Frontend: Angular 21, TypeScript, RxJS.
- Packaging: backend uses `setuptools`; frontend uses npm with `package-lock.json`.
- Container runtime: Docker Compose with separate backend and frontend services.

## Backend Dependencies

- Production: `fastapi>=0.110`, `uvicorn>=0.27`.
- Development/test: `pytest>=8.0`, `httpx>=0.28`.
- CLI entry point: `notion-meeting-to-obsidian`.

## Frontend Dependencies

- Angular packages: `@angular/*` 21.2.x.
- Runtime helpers: `rxjs`, `tslib`, `zone.js`.
- Build tooling: `@angular-devkit/build-angular`, `@angular/cli`, `typescript`.
- Overrides: `postcss`, `uuid`.

## Environment

Required variables are `NOTION_TOKEN`, `NOTION_SOURCE_ID`, and `OBSIDIAN_VAULT_PATH`.
Docker also uses `HOST_OBSIDIAN_VAULT_PATH` to mount the host vault into `/vault`.
Ports are configurable with `BIND_HOST`, `FRONTEND_PORT`, and `BACKEND_PORT`.

## Evidence

- `backend/pyproject.toml`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.env.example`
- `docker-compose.yml`
