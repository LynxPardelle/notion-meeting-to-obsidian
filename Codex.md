# Development Memory

## Codex Workflow
- Start every Codex session in this repository by running:

```powershell
git pull --rebase --autostash
```

- Before ending a completed work session, ask the user for permission before pushing changes to the remote repository.
- Do not push without explicit user approval.

## Current Local Setup
- Docker Compose defaults to backend `http://127.0.0.1:8765`.
- Docker Compose defaults to frontend `http://127.0.0.1:47863`.
- Ports are configurable with `BACKEND_PORT`, `FRONTEND_PORT`, and `BIND_HOST`.
- The frontend calls `/api`; Docker Nginx proxies `/api` to backend, and local `npm start` uses `frontend/proxy.conf.js`.
- The local `.env` file is ignored by Git and contains machine-specific values and secrets.

## Current Architecture Notes
- Work from `development` unless the user explicitly asks to promote to `main`.
- Sync is delta-oriented: skip unchanged notes, avoid timestamp-only rewrites, and delete only known Notion-generated stale files.
- Meeting card fields are `Resumen`, `Tareas`, and `Notas`; raw Markdown remains editable.
- Table schemas are exposed through `/note-sources/schema` and drive the properties/mapping UI.
