# Conventions

## Python

- Source lives under `backend/src/notion_meeting_to_obsidian`.
- Tests live under `backend/tests`.
- Code uses type hints and small focused modules.
- Dataclasses are used for sync result/state payload shapes where appropriate.
- Errors from Notion are wrapped in `NotionApiError`.
- Runtime configuration errors use `ConfigError`.

## Frontend

- Angular standalone-style root component is implemented in `app.component.*`.
- API response shapes are typed in `api.service.ts`.
- The frontend calls relative `/api` paths rather than hardcoded backend URLs.
- Theme and layout styles are centralized in `frontend/src/styles.css`.

## Configuration

- Secrets and machine-specific paths belong in `.env`, never in Git.
- `.env.example` is the source of truth for required and optional environment variables.
- Docker maps the host Obsidian vault to `/vault`.
- `FRONTEND_PORT`, `BACKEND_PORT`, and `BIND_HOST` should be used instead of hardcoded host ports.

## Git

- Active development happens on `development`.
- `main` is treated as stable/release-ready.
- `master` is legacy and should not be used for new work unless the maintainer says otherwise.

## Documentation

- Update `README.md`, `docs/application-guide.md`, `docs/setup-from-github.md`, and `AGENTS.md` when setup, ports, architecture, sync behavior, or agent workflow changes.
- Keep `docs/codebase/` aligned with actual files, not intended future work.

## Evidence

- `backend/pyproject.toml`
- `backend/src/notion_meeting_to_obsidian/*.py`
- `backend/tests/*.py`
- `frontend/src/app/api.service.ts`
- `frontend/src/app/app.component.ts`
- `.env.example`
- `.gitignore`
- `AGENTS.md`
