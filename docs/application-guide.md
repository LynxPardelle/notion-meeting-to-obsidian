# Application Guide

This project syncs meeting notes from Notion into an Obsidian vault as Markdown files. It has three parts:

- A Python sync engine that talks to the official Notion API.
- A FastAPI backend that exposes local HTTP endpoints for sync, read, and save.
- An Angular frontend for browsing the synced tree, editing Markdown, and previewing notes.

## Runtime Flow

1. The app reads configuration from environment variables or `.env`.
2. The sync engine loads the previous sync state from `.notion-meeting-sync/state.json` inside the Obsidian vault.
3. The Notion source is resolved as one of these modes:
   - `NOTION_SOURCE_IDS`: a comma-separated list of selected pages or databases.
   - `NOTION_SOURCE_ID`: a single page or database.
   - `NOTION_SYNC_ALL_ACCESSIBLE=true`: every page visible to the integration.
4. Page trees are traversed through Notion `child_page` blocks.
5. Each Notion page is converted to Markdown.
6. Markdown is written to `OBSIDIAN_VAULT_PATH/OBSIDIAN_MEETINGS_FOLDER` only when the note is new, moved, renamed, or semantically changed.
7. The sync state is updated with page IDs, last edited timestamps, and output paths.
8. Files that were previously synced but no longer exist in the selected Notion source tree are deleted when `OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true`.

## Notion Hierarchy

Notion represents child pages as blocks of type `child_page`. The sync engine follows those blocks recursively.

Example:

```txt
Documento Padre
  Nota Hijo
```

Output in Obsidian:

```txt
Meetings/
  Documento Padre/
    Documento Padre.md
    Nota Hijo.md
```

When a Notion page has child pages, the parent Markdown file is written inside its own folder. This keeps Obsidian from showing a same-name folder and same-name note side by side at the root level.

## Obsidian Delta And Mirror Behavior

The Obsidian `Meetings` folder is treated as a managed mirror for Notion-generated Markdown files, not as a blind delete-and-recreate target.

When `OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true`, the app deletes a Markdown file when all of these are true:

- The file is inside the configured `Meetings` folder.
- The file has a `.md` extension.
- The file path is not one of the active output paths produced by the current Notion sync, or the file belongs to a stale synced page in state.
- The file is known to be Notion-generated, usually because it has `notion_id` in YAML frontmatter or because it was tracked in `.notion-meeting-sync/state.json`.

Manual `.md` files without Notion frontmatter are left alone. It is still cleaner to keep personal notes outside `Meetings`, because that folder is primarily intended for synchronized meeting notes.

The sync also avoids unnecessary writes. If Notion changes only volatile metadata such as `last_edited_time` or `synced_at`, but the rendered Markdown body and stable frontmatter are unchanged, the file is skipped and only the local state is updated.

If a page moves from root to child, or from one parent to another, the old synced file is removed after the new file is written. This prevents duplicate notes such as an old root note plus the new nested note.

## Configuration

Required:

```txt
NOTION_TOKEN=secret_xxx
NOTION_SOURCE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OBSIDIAN_VAULT_PATH=C:\Users\you\Documents\ObsidianVault
```

Common optional variables:

```txt
NOTION_SOURCE_IDS=id_1,id_2,id_3
OBSIDIAN_MEETINGS_FOLDER=Meetings
HOST_OBSIDIAN_VAULT_PATH=C:\Users\you\Documents\ObsidianVault
SYNC_STATE_PATH=
NOTION_SYNC_ALL_ACCESSIBLE=false
OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true
BIND_HOST=127.0.0.1
FRONTEND_PORT=47863
BACKEND_PORT=8765
CORS_ALLOW_ORIGINS=
```

Notes:

- `NOTION_TOKEN` must be kept out of Git.
- `NOTION_SOURCE_IDS` is the recommended mode when you want precise control.
- `HOST_OBSIDIAN_VAULT_PATH` is used by Docker Compose to mount the Windows vault path into the backend container.
- Inside Docker, the backend sees the vault as `/vault`.
- `FRONTEND_PORT` and `BACKEND_PORT` control the ports exposed on the host machine.

## Backend API

Default base URL:

```txt
http://127.0.0.1:8765
```

Endpoints:

- `GET /health`: returns backend health.
- `POST /sync?force=false`: syncs Notion into Obsidian.
- `GET /notes`: lists Markdown files currently active in the synced state.
- `GET /note-sources`: lists Notion tables/data sources found in state.
- `GET /note-sources/schema`: lists detected table schemas and the app's field mapping.
- `GET /notes/read?path=...`: reads one Markdown file from the meetings folder.
- `POST /notes/save`: saves edited Markdown back to disk.
- `POST /notes/card/save`: saves editable meeting-card sections back to Markdown.
- `POST /draft`: converts one Notion page to Markdown without writing it to the vault.

## Frontend

Default URL:

```txt
http://127.0.0.1:47863
```

Main behaviors:

- `Sync` calls the backend and updates Obsidian.
- `Refresh` reloads the visible Markdown files from disk.
- The left sidebar renders parent and child notes as a collapsible tree.
- Tree groups load collapsed by default.
- Selecting a note opens the meeting card view by default.
- The meeting card exposes editable `Resumen`, `Tareas`, and `Notas` sections.
- `Editar Markdown` opens the raw Markdown editor.
- Save actions write changes back to the configured Obsidian file.
- The properties panel adapts to the source table schema and hides duplicated mapped summary data.

## Docker

Start both services:

```powershell
docker compose up --build
```

Ports:

- Frontend: `127.0.0.1:${FRONTEND_PORT:-47863}`
- Backend: `127.0.0.1:${BACKEND_PORT:-8765}`

Docker Compose mounts:

```txt
HOST_OBSIDIAN_VAULT_PATH -> /vault
```

The backend container writes Markdown to:

```txt
/vault/Meetings
```

which maps back to the Windows Obsidian vault path.

## Local Development

Backend:

```powershell
cd backend
python -m pip install -e ".[dev]"
python -m pytest
notion-meeting-to-obsidian serve
```

Frontend:

```powershell
cd frontend
npm install
npm start
```

## Troubleshooting

If a Notion page does not appear:

- Confirm the integration has access to the page.
- Confirm the page ID is in `NOTION_SOURCE_IDS`, or enable `NOTION_SYNC_ALL_ACCESSIBLE=true`.
- Run `POST /sync?force=true` or press `Sync` in the frontend.

If old files remain in Obsidian:

- Confirm `OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true`.
- Run a forced sync after deleting or unsharing the Notion page.
- Confirm the file is inside `OBSIDIAN_MEETINGS_FOLDER`; the sync only cleans that folder.
- Confirm the stale file has Notion frontmatter or exists in `.notion-meeting-sync/state.json`; manual Markdown files are intentionally preserved.

If Docker commands are not found on Windows:

```powershell
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
docker --version
docker compose version
```
