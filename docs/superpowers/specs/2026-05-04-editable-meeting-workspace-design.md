# Editable Meeting Workspace Design

## Context

The application currently syncs pages from a Notion source into Markdown files stored in an Obsidian vault. The frontend shows a note tree, Markdown content, preview, and Notion metadata. The next product step is to make the meeting view useful for non-technical users while preserving full Markdown control for advanced users.

This design keeps Notion as the remote source of meeting data and Obsidian Markdown files as the local editable source for this stage. Writing edited content back to Notion is intentionally out of scope for now because Notion stores content as blocks rather than raw Markdown.

## Goal

Create a meeting workspace where the first screen is a readable and editable meeting card, not a raw Markdown editor. Users can edit only the meeting sections that matter in this stage:

- Summary
- Tasks
- Notes

Users can also open a full Markdown editor when they need complete control. Both editing modes save changes into the same `.md` file in the Obsidian vault.

## Non-Goals

- Do not write changes back to Notion in this stage.
- Do not edit Notion database properties such as date, people, status, tags, or project.
- Do not assume user-specific names, workspaces, or database column names in code.
- Do not replace the existing Markdown workflow; extend it with a friendlier editable card.

## User Experience

The primary screen should behave like a meeting workspace with three areas on desktop:

1. Meeting navigation on the left.
2. Editable meeting card in the center.
3. Notion and Obsidian metadata on the right.

The center panel opens in card mode by default. It shows the meeting title, useful metadata, then editable sections for summary, tasks, and notes. A secondary action opens the full Markdown editor.

On mobile, the same information should be available through compact tabs:

- Meetings
- Card
- Details

The theme switch remains compact and should work consistently on desktop and mobile.

## Meeting Card Mode

Card mode is the default view for a selected meeting. It should show:

- Title
- Optional date, participants, and source metadata when available
- Summary editor
- Tasks editor
- Notes editor
- Save changes button
- Edit Markdown button
- Open in Notion action when a Notion URL exists
- Obsidian path display

The editable card writes only to Markdown sections. Metadata from Notion remains read-only in this stage.

## Markdown Mode

Markdown mode is the advanced editing view. It should show the full `.md` file with:

- Markdown editor
- Preview
- Save button
- Cancel/back to card action

After saving Markdown mode, the frontend should reload the note data and rebuild the meeting card from the updated file.

## Markdown Section Contract

The app needs a predictable Markdown structure to support structured editing. It should recognize these headings:

```md
## Resumen

## Tareas

## Notas
```

For English or future multilingual support, the parser can later support aliases such as `## Summary`, `## Tasks`, and `## Notes`, but the first implementation should prioritize the Spanish section names used in this product flow.

If a synced note does not contain one or more of these sections, the app should still render empty editable fields and create the missing sections when saving.

Task lines should support standard Markdown checkboxes:

```md
- [ ] Pending task
- [x] Completed task
```

The card should preserve task checked state. Non-checkbox task text can be treated as plain task text when needed.

## Data Flow

1. Backend syncs Notion pages into Obsidian `.md` files.
2. Frontend fetches note list and selected note content.
3. Backend parses selected Markdown into structured card sections.
4. Frontend renders summary, tasks, and notes in editable card mode.
5. User edits one or more card fields.
6. Frontend sends structured changes to backend.
7. Backend updates the same `.md` file, preserving frontmatter, title, metadata, and unrelated sections.
8. Frontend refetches the note and displays the updated card.

Markdown mode follows the existing full-file editing pattern, then triggers the same refetch and card parsing.

## Backend Design

Add a Markdown section parser/writer with clear boundaries:

- Parse frontmatter separately from body.
- Detect target sections by level-two headings.
- Extract summary, tasks, and notes.
- Update only those sections when saving from card mode.
- Preserve unknown sections and raw Markdown outside the editable sections.
- Create missing sections in a stable order near the main meeting content.

Expose API support for structured card editing:

- Read selected note with parsed card sections.
- Save structured card sections back to the `.md` file.

Existing full Markdown save behavior should remain available.

## Frontend Design

The selected note view should have two states:

- Card mode
- Markdown mode

Card mode should be the default. It should be optimized for readability and quick editing:

- Summary as a multiline text area.
- Tasks as editable checkbox rows with add/remove controls.
- Notes as a multiline text area.
- Save button disabled until changes exist.
- Unsaved changes warning when switching note or mode.

Markdown mode should keep the full editor and preview behavior, but it should feel secondary to the meeting card.

The metadata panel should display all available Notion database properties generically. The UI should not depend on specific column names such as `Texto`, `Fecha`, or a specific person's name.

## Error Handling

The app should handle:

- Missing Markdown file.
- Empty or malformed Markdown.
- Missing editable sections.
- File write errors.
- Note changed on disk after frontend loaded it.
- Notion metadata missing or unavailable.

For this stage, if the file changed on disk after load, the safest behavior is to warn the user and ask them to refresh before saving, instead of silently overwriting.

## Testing

Backend tests should cover:

- Parsing Markdown with all three sections.
- Parsing Markdown with missing sections.
- Preserving frontmatter and unrelated sections.
- Updating only summary, tasks, and notes.
- Creating missing sections on save.
- Preserving checkbox task states.

Frontend tests should cover:

- Card mode is the default selected-note view.
- Editing summary, tasks, and notes enables save.
- Save calls the structured card endpoint.
- Markdown mode remains available.
- Metadata renders generically from available fields.

Manual verification should include:

- Save from card mode and confirm Obsidian shows the updated `.md`.
- Save from Markdown mode and confirm card mode refreshes.
- Test desktop and mobile layouts.
- Test light and dark themes.

## Rollout

Implement this as one focused stage:

1. Add backend parser/writer and tests.
2. Add structured API endpoint.
3. Update frontend selected-note view to card-first UX.
4. Keep full Markdown editor behind the Edit Markdown action.
5. Verify Docker, backend tests, frontend build, and local browser behavior.

## Open Follow-Up

Syncing edits back to Notion remains a future design topic. That stage needs a separate decision because Markdown must be converted into Notion blocks or mapped into specific database fields.
