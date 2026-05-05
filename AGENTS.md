# AGENTS.md

Operational context for AI agents and contributors working on `notion-meeting-to-obsidian`.

## Project Summary

This repository is a local tool that syncs Notion Meeting AI notes into Obsidian-compatible Markdown.

- Backend: Python 3.11+, FastAPI, Uvicorn, Pytest.
- Frontend: Angular, TypeScript, RxJS.
- Integration: official Notion REST API.
- Output: Markdown files written into a local Obsidian vault.
- Runtime model: local-first; Docker defaults to backend `127.0.0.1:8765` and frontend `127.0.0.1:47863`, both configurable through environment variables.

## Repository Layout

- `backend/`: Python package, CLI, FastAPI API, Notion client, sync orchestration, Markdown conversion, state handling, writer, tests.
- `frontend/`: Angular editor UI for sync, note list, Markdown editing, preview, and save actions.
- `docs/`: user guides, audits, implementation notes, and project context.
- `docs/codebase/`: generated codebase knowledge for humans and AI agents.
- `docker-compose.yml`: local container orchestration when using Docker.

## Branching Workflow

Use this branch flow:

1. Feature or fix branches start from `development`.
2. Merge completed work into `development`.
3. Promote validated work from `development` to `testing`.
4. Promote release-ready work from `testing` to `main`.

Branch meanings:

- `main`: stable/default branch for users cloning the repository.
- `testing`: QA/pre-release validation branch.
- `development`: active integration branch.
- `master`: legacy branch kept for history; do not use for new work unless the maintainer says otherwise.

Do not push directly to `main` unless the maintainer explicitly approves it. Prefer pull requests.

## Setup Commands

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Run the backend API:

```powershell
cd backend
notion-meeting-to-obsidian serve
```

Run a sync from CLI:

```powershell
cd backend
notion-meeting-to-obsidian sync
```

Frontend:

```powershell
cd frontend
npm install
npm start
```

Docker:

```powershell
docker compose up -d
```

Open the app at `http://127.0.0.1:47863` unless `FRONTEND_PORT` is changed in `.env`.

## Environment Variables

Required:

- `NOTION_TOKEN`
- `NOTION_SOURCE_ID`
- `OBSIDIAN_VAULT_PATH`

Optional:

- `OBSIDIAN_MEETINGS_FOLDER`
- `SYNC_STATE_PATH`
- `HOST_OBSIDIAN_VAULT_PATH`
- `NOTION_SOURCE_IDS`
- `NOTION_SYNC_ALL_ACCESSIBLE`
- `OBSIDIAN_DELETE_STALE_SYNCED_NOTES`
- `BIND_HOST`
- `FRONTEND_PORT`
- `BACKEND_PORT`
- `CORS_ALLOW_ORIGINS`

Use `.env.example` as the template. Never commit real `.env` files or secrets.

## Architecture Notes

Backend responsibilities:

- Read and validate runtime configuration.
- Query Notion database pages and block children.
- Detect new or changed pages using `last_edited_time`.
- Use delta-style local file updates: unchanged Markdown is skipped, timestamp-only changes do not rewrite files, and cleanup targets known Notion-generated files.
- Convert Notion content into Markdown with YAML frontmatter.
- Write Markdown files into the configured Obsidian vault folder.
- Persist sync state in JSON.
- Expose local FastAPI endpoints for the frontend.

Frontend responsibilities:

- Call the local backend API.
- Display synced notes.
- Let the user open, edit, preview, and save Markdown.
- Avoid duplicating backend sync or conversion logic.

## Important Files

- `backend/src/notion_meeting_to_obsidian/config.py`: environment config.
- `backend/src/notion_meeting_to_obsidian/notion.py`: Notion REST client.
- `backend/src/notion_meeting_to_obsidian/converter.py`: Notion-to-Markdown conversion.
- `backend/src/notion_meeting_to_obsidian/writer.py`: safe Markdown file writes.
- `backend/src/notion_meeting_to_obsidian/state.py`: incremental sync state.
- `backend/src/notion_meeting_to_obsidian/sync.py`: sync orchestration.
- `backend/src/notion_meeting_to_obsidian/api.py`: FastAPI app.
- `backend/src/notion_meeting_to_obsidian/cli.py`: CLI entrypoint.
- `frontend/src/app/api.service.ts`: frontend API client.
- `frontend/src/app/app.component.ts`: main Angular UI behavior.
- `frontend/nginx.conf`: serves the built Angular app and proxies `/api` to the backend in Docker.
- `frontend/scripts/start-dev-server.mjs`: loads `.env` and starts Angular dev server with dynamic ports.

## Testing Expectations

Before claiming backend work is complete, run:

```powershell
cd backend
python -m pytest
```

Before claiming frontend work is complete, run:

```powershell
cd frontend
npm run build
```

When touching API contracts, verify both backend endpoints and frontend callers.

When touching sync behavior, add or update tests in `backend/tests/test_sync.py` before changing production code.

## Safety Rules For AI Agents

- Read relevant files before editing.
- Keep changes scoped to the requested task.
- Do not invent project behavior; cite source files when explaining.
- Do not commit secrets, local vault contents, `.env`, caches, build outputs, or virtual environments.
- Do not rewrite git history or delete branches unless the maintainer explicitly asks.
- Do not push to the remote without explicit maintainer approval.
- If working locally, start from `development` unless instructed otherwise.
- If branch protection is unavailable, still follow the PR workflow manually.
- Keep `docs/codebase/` and this file current when architecture, setup, sync behavior, or environment variables change.

## Known Context

The intended flow is Notion Meeting AI to Markdown to Obsidian, with optional review/editing in the Angular UI. The project is local-first and should not require a hosted backend for normal use. The frontend calls `/api`; Docker's Nginx proxy forwards that to the backend service, while local `npm start` uses `frontend/proxy.conf.js`.

GitHub branch protection for private repositories may require a paid GitHub plan. If protection is unavailable, treat `main` as socially locked: only merge into it after review and testing.
