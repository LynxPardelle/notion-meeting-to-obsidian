# Notion Meeting AI to Obsidian

Local tool for syncing Notion Meeting AI notes into Obsidian-compatible Markdown.

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

`NOTION_TOKEN`, `NOTION_SOURCE_ID`, and `OBSIDIAN_VAULT_PATH` are required. The token is never stored in source control.

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

## What The First Version Does

- Queries a Notion database source through the official API.
- Detects new or changed pages using `last_edited_time`.
- Converts common Notion blocks into Markdown.
- Writes `.md` files into `OBSIDIAN_VAULT_PATH\OBSIDIAN_MEETINGS_FOLDER`.
- Provides a local API and Angular editor for reviewing and saving notes.

## Tests

```powershell
cd backend
python -m pytest
```
