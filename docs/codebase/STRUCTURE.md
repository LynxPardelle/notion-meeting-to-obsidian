# Structure

## Root

- `README.md`: top-level overview, setup, Docker, tests.
- `AGENTS.md`: operational context for AI agents and contributors.
- `Codex.md`: local Codex memory and workflow notes.
- `.env.example`: environment variable template.
- `docker-compose.yml`: local container orchestration.

## Backend

- `backend/src/notion_meeting_to_obsidian/config.py`: environment configuration.
- `backend/src/notion_meeting_to_obsidian/notion.py`: Notion REST client.
- `backend/src/notion_meeting_to_obsidian/converter.py`: Notion blocks to Markdown conversion.
- `backend/src/notion_meeting_to_obsidian/meeting_card.py`: editable card section parsing and updates.
- `backend/src/notion_meeting_to_obsidian/metadata.py`: Notion property metadata formatting.
- `backend/src/notion_meeting_to_obsidian/state.py`: sync state persistence.
- `backend/src/notion_meeting_to_obsidian/sync.py`: sync orchestration.
- `backend/src/notion_meeting_to_obsidian/writer.py`: safe Markdown filenames and writes.
- `backend/src/notion_meeting_to_obsidian/api.py`: FastAPI app.
- `backend/src/notion_meeting_to_obsidian/cli.py`: CLI entry point.
- `backend/tests/`: Pytest suite.

## Frontend

- `frontend/src/app/api.service.ts`: HTTP client and shared API types.
- `frontend/src/app/app.component.ts`: main UI state and interactions.
- `frontend/src/app/app.component.html`: app template.
- `frontend/src/styles.css`: global styles and theme tokens.
- `frontend/nginx.conf`: Docker Nginx static hosting and `/api` proxy.
- `frontend/proxy.conf.js`: Angular dev-server `/api` proxy.
- `frontend/scripts/start-dev-server.mjs`: loads `.env` and starts Angular with dynamic ports.

## Documentation

- `docs/application-guide.md`: product/runtime guide.
- `docs/setup-from-github.md`: install guide for new machines.
- `docs/audits/`: audit notes.
- `docs/superpowers/`: implementation specs and plans.
- `docs/codebase/`: codebase memory for humans and AI agents.

## Evidence

- `backend/src/notion_meeting_to_obsidian/*.py`
- `frontend/src/app/*`
- `frontend/nginx.conf`
- `frontend/proxy.conf.js`
- `frontend/scripts/start-dev-server.mjs`
