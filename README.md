# Notion Meeting AI to Obsidian

Local tool for syncing Notion Meeting AI notes into Obsidian-compatible Markdown.

Full documentation is in [docs/application-guide.md](docs/application-guide.md).

## Stack

- Python CLI and FastAPI backend
- Angular frontend
- Official Notion API
- Obsidian vault output through environment variables

## Environment

Copy `.env.example` to `.env` or set these variables in your shell:

```powershell
$env:NOTION_TOKEN="secret_xxx"
$env:NOTION_SOURCE_ID="your_notion_database_id"
$env:OBSIDIAN_VAULT_PATH="C:\Users\you\Documents\ObsidianVault"
$env:OBSIDIAN_MEETINGS_FOLDER="Meetings"
```

`NOTION_TOKEN`, `NOTION_SOURCE_ID`, and `OBSIDIAN_VAULT_PATH` are required. `NOTION_SOURCE_ID` can be a Notion database ID or a single page ID. The token is never stored in source control.

Use `NOTION_SOURCE_IDS=id_1,id_2` when you want to sync only a selected set of Notion pages/databases. This keeps old or unrelated shared pages out of the local app view.

Set `NOTION_SYNC_ALL_ACCESSIBLE=true` to sync every page currently shared with the integration, using each visible top-level page as a root.

`OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true` is the default mirror behavior. It removes Markdown files inside the configured meetings folder when they are not part of the current Notion source tree. Keep manual notes outside that folder if they should never be touched by sync.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
notion-meeting-to-obsidian sync
notion-meeting-to-obsidian serve
```

The API defaults to `http://127.0.0.1:8765`.

## Frontend

```powershell
cd frontend
npm install
npm start
```

The Angular app calls the local backend. Start the backend before using the UI.

## Docker

Create a local `.env` file from `.env.example`. For Docker, keep your Windows vault path in `HOST_OBSIDIAN_VAULT_PATH`; the backend container writes to `/vault`.

```powershell
copy .env.example .env
```

Example Docker values:

```txt
NOTION_TOKEN=secret_xxx
NOTION_SOURCE_ID=your_notion_database_id
HOST_OBSIDIAN_VAULT_PATH=C:\Users\you\Documents\ObsidianVault
OBSIDIAN_MEETINGS_FOLDER=Meetings
```

Run both services:

```powershell
docker compose up --build
```

Then open:

- Frontend: `http://127.0.0.1:4200`
- Backend health: `http://127.0.0.1:8765/health`

The Compose file maps `HOST_OBSIDIAN_VAULT_PATH` to `/vault` and sets `OBSIDIAN_VAULT_PATH=/vault` inside the backend container. Do not put your Notion token in the Docker image.

## What The First Version Does

- Queries a Notion database source or a single Notion page through the official API.
- Recursively follows Notion child pages and writes parent pages inside their own child folders for cleaner Obsidian browsing.
- Detects new or changed pages using `last_edited_time`.
- Converts common Notion blocks into Markdown.
- Writes `.md` files into `OBSIDIAN_VAULT_PATH\OBSIDIAN_MEETINGS_FOLDER`.
- Deletes stale synced files when the corresponding Notion page is no longer present.
- Provides a local API and Angular editor for reviewing and saving notes.

## Tests

```powershell
cd backend
python -m pytest
```
