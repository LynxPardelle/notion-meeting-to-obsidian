# Automation, Theme, and Notion Database Design

## Goal

Evolve the local Notion Meeting AI to Obsidian converter from a manual sync tool into a more comfortable team workflow. The next version should improve the visual note tree, add a user-selectable theme, introduce local automatic synchronization, and document the recommended Notion database setup for team meeting notes.

## Scope

This design covers the next development cycle only:

- Visual hierarchy for nested notes at any practical depth.
- Collapsed note groups by default.
- Light, dark, and system theme preferences.
- Local automatic sync by interval.
- A sync status surface in the API and Angular app.
- Documentation and configuration guidance for a root Notion database such as `Meeting Notes Inbox`.

This design does not implement public Notion webhooks, cloud hosting, authentication for multiple users, or direct VS Code/Codex automation. Those are later phases after the local workflow is stable.

## Product Direction

The recommended team flow is:

```txt
Notion workspace or teamspace
  Database: Meeting Notes Inbox
    Meeting note page
    Meeting note page
    Meeting note page

Local app
  Syncs the database or root page through the Notion API
  Writes Markdown files into the Obsidian vault
  Shows the same hierarchy in the Angular interface
```

The current page-root flow remains supported because it already works for the user's existing notes. The database-root flow becomes the recommended setup for teams because it gives a stable inbox for meeting notes, works better with Notion properties, and avoids manually sharing one note at a time.

## User Experience

### Note Tree

The Angular sidebar should show the real hierarchy of synced notes:

```txt
Meeting Notes
  Clase Python
    Documento Padre
      Nota Hijo
        Nota Nieto
```

All expandable groups should start collapsed when the app loads or when the note list is refreshed. The user can open only the branch they want to inspect. The tree should support deeper levels using indentation, disclosure controls, and stable spacing so child, grandchild, and deeper notes are visually distinct.

### Theme Preference

The app should provide a compact theme control with three modes:

- `Claro`
- `Oscuro`
- `Sistema`

The selected mode should persist in `localStorage`. `Sistema` should follow the browser or operating system color preference. The implementation should use CSS variables so the editor, preview, sidebar, buttons, empty states, and status messages share the same theme tokens.

### Sync Status

The interface should show whether automatic sync is enabled, when the last sync happened, and whether the last sync failed. Manual `Sync` remains available because it is useful while testing or when the user wants an immediate update.

Example status copy:

```txt
Auto-sync activo · Ultimo sync hace 2 min
```

If sync fails, the UI should show a concise error and keep the previous note list visible.

## Backend Design

### Configuration

Add optional environment variables:

```txt
AUTO_SYNC_ENABLED=false
AUTO_SYNC_INTERVAL_SECONDS=300
```

Future-compatible configuration can be documented but not required in the first implementation:

```txt
NOTION_SOURCE_IDS=id1,id2,id3
```

`NOTION_SOURCE_ID` remains the primary supported variable for this cycle.

### Automatic Sync

The FastAPI backend should start a local background sync loop only when `AUTO_SYNC_ENABLED=true`. The loop should:

- Wait for the configured interval between runs.
- Avoid overlapping syncs if a manual sync or previous automatic sync is still running.
- Reuse the existing sync orchestration instead of duplicating Notion or writer logic.
- Store the last sync result in memory for the UI.
- Log errors without crashing the server.

This is intentionally local polling. Public Notion webhooks are excluded from this cycle because they require a public HTTPS callback endpoint and a different deployment model.

### API

Keep the existing manual sync endpoint. Add:

```txt
GET /sync/status
```

The response should include:

```json
{
  "auto_sync_enabled": true,
  "interval_seconds": 300,
  "running": false,
  "last_started_at": "2026-05-01T18:00:00Z",
  "last_finished_at": "2026-05-01T18:00:05Z",
  "last_success": true,
  "last_error": null,
  "last_synced_count": 4
}
```

If the current sync code does not expose a count, the first version may return `null` for `last_synced_count` and add counting later.

## Frontend Design

The Angular app should keep its current operational layout: sidebar, editor, preview, and actions. The next changes should stay focused:

- Add a theme control near the existing header/actions.
- Refactor the note tree rendering so each node receives a depth value.
- Use the depth value for indentation and connector styling.
- Store collapsed/expanded state by stable path or note id.
- Initialize all expandable nodes as collapsed.
- Poll `GET /sync/status` on a lightweight interval while the app is open.
- Refresh the note list after successful manual sync and after completed automatic sync if the last finish time changed.

The frontend should not assume a maximum hierarchy depth. It should render any depth the backend provides, with practical CSS limits for readability.

## Obsidian Behavior

The Obsidian vault remains the source of generated `.md` files for local use. Synced files should continue to be stored under `OBSIDIAN_VAULT_PATH/OBSIDIAN_MEETINGS_FOLDER`.

The existing strict mirror behavior should remain:

```txt
OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true
```

When enabled, synced notes no longer present in the active Notion source should be removed from the synced meetings folder. User-created notes should be kept outside that generated folder to avoid accidental deletion.

## Notion Database Setup

Documentation should explain the difference between:

- A Notion meeting note page.
- A Notion page that contains child pages.
- A Notion database that contains meeting note pages.

The recommended setup for teams is a database named `Meeting Notes Inbox`. The user should share that database with the internal integration and use its id as `NOTION_SOURCE_ID`.

The app should continue to support a page id as `NOTION_SOURCE_ID`, but documentation should mark a database id as the preferred team setup.

## Error Handling

- If the Notion API token is invalid, show a clear backend error and UI message.
- If the source id is not shared with the integration, report that the app cannot access the configured source.
- If the Obsidian vault path is missing or not writable, fail sync with a clear message.
- If automatic sync fails, keep the backend running and expose the last error through `/sync/status`.
- If the frontend cannot reach the backend, keep the editor surface visible and show connection status.

## Testing

Backend tests should cover:

- Config parsing for automatic sync variables.
- Sync status defaults.
- Non-overlapping sync behavior.
- `/sync/status` response shape.
- Existing writer behavior for stale note deletion.

Frontend tests or build verification should cover:

- Theme preference application.
- Default collapsed state for tree groups.
- Depth-based rendering for child and grandchild notes.
- Status API integration.

Manual verification should include:

- `python -m pytest` in `backend`.
- `npm run build` in `frontend`.
- Docker Compose build.
- Browser check of light mode, dark mode, collapsed tree, manual sync, and status display.

## Phasing

### Sprint 1

- Fix deep tree hierarchy rendering.
- Collapse groups by default.
- Add light/dark/system theme support.
- Verify edit and save still write to Obsidian files.

### Sprint 2

- Add automatic sync configuration.
- Add backend sync status state and endpoint.
- Show sync status in Angular.
- Add backend and frontend verification.

### Sprint 3

- Improve documentation for `Meeting Notes Inbox`.
- Document page source versus database source.
- Prepare configuration notes for future `NOTION_SOURCE_IDS`.
- Re-run Docker and local app verification.

## Open Decisions

No blocking product decisions remain for this cycle. The chosen direction is local-first, interval-based automation with a Notion database as the recommended team source and the current page-root workflow preserved for compatibility.
