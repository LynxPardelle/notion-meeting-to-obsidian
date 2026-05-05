# Architecture

## Overview

The app is local-first. A Python backend syncs Notion content to local Markdown files in an Obsidian vault. An Angular frontend talks to the backend over local HTTP and provides browsing/editing UI.

## Data Flow

1. Configuration is read from environment variables.
2. `MeetingSyncService` resolves Notion sources as selected IDs, one source ID, or all accessible pages.
3. The Notion client queries databases/data sources or falls back to page sources.
4. Page trees are traversed through `child_page` blocks.
5. Blocks are converted to Markdown with YAML frontmatter.
6. Markdown is written to the Obsidian meetings folder only when needed.
7. Sync state is stored as JSON under `.notion-meeting-sync/state.json`.
8. The frontend reads notes and schemas through `/api` endpoints.

## Backend Layers

- Configuration: `Config.from_env`.
- Integration: `NotionClient`.
- Domain/sync: `MeetingSyncService`, `SyncState`.
- Conversion: `converter.py`, `metadata.py`, `meeting_card.py`.
- Persistence: filesystem writes in `writer.py` and state JSON in `state.py`.
- API: `api.py`.
- CLI: `cli.py`.

## Frontend Layers

- API boundary: `ApiService`.
- State/UI orchestration: `AppComponent`.
- Presentation: `app.component.html` and `styles.css`.
- Runtime proxy:
  - Docker: Nginx proxies `/api` to `backend:8765`.
  - Local dev: Angular proxy forwards `/api` to `BACKEND_PORT`.

## Sync Strategy

The sync is delta-oriented:

- Existing state uses `last_edited_time` to skip unchanged pages.
- If Notion timestamps change but rendered Markdown is semantically identical, the local file is not rewritten.
- Cleanup removes stale files tracked by state or known to be Notion-generated through `notion_id` frontmatter.
- Manual Markdown files without Notion frontmatter are preserved.

## Evidence

- `backend/src/notion_meeting_to_obsidian/config.py`
- `backend/src/notion_meeting_to_obsidian/notion.py`
- `backend/src/notion_meeting_to_obsidian/sync.py`
- `backend/src/notion_meeting_to_obsidian/state.py`
- `backend/src/notion_meeting_to_obsidian/converter.py`
- `backend/src/notion_meeting_to_obsidian/api.py`
- `frontend/src/app/api.service.ts`
- `frontend/src/app/app.component.ts`
- `frontend/nginx.conf`
- `frontend/proxy.conf.js`
