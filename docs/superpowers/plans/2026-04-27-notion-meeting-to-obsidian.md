# Notion Meeting to Obsidian Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python and Angular tool that syncs Notion Meeting AI notes into editable Obsidian Markdown files.

**Architecture:** The Python backend owns configuration, Notion access, Markdown conversion, file writes, state, CLI, and FastAPI endpoints. The Angular frontend calls the local API to sync, preview, edit, and save notes without duplicating conversion logic.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pytest, Angular, TypeScript.

---

### Task 1: Repository Foundation

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/src/notion_meeting_to_obsidian/__init__.py`

- [x] **Step 1: Create repository documentation and configuration**

Add a README with setup, environment variables, CLI commands, API server command, and frontend command. Add `.env.example` with `NOTION_TOKEN`, `NOTION_SOURCE_ID`, `OBSIDIAN_VAULT_PATH`, `OBSIDIAN_MEETINGS_FOLDER`, and `SYNC_STATE_PATH`.

- [x] **Step 2: Create backend package metadata**

Define a Python package named `notion-meeting-to-obsidian` with console script `notion-meeting-to-obsidian`.

### Task 2: Backend Core

**Files:**
- Create: `backend/src/notion_meeting_to_obsidian/config.py`
- Create: `backend/src/notion_meeting_to_obsidian/converter.py`
- Create: `backend/src/notion_meeting_to_obsidian/state.py`
- Create: `backend/src/notion_meeting_to_obsidian/writer.py`
- Create: `backend/tests/test_converter.py`
- Create: `backend/tests/test_state_writer.py`

- [x] **Step 1: Implement environment configuration**

`Config.from_env()` reads required variables and raises `ConfigError` listing any missing names.

- [x] **Step 2: Implement Markdown conversion**

Support title extraction, YAML frontmatter, paragraphs, headings, bulleted lists, numbered lists, to-do blocks, quotes, code, dividers, and basic links.

- [x] **Step 3: Implement state and writer**

Store page sync metadata in JSON. Write Markdown to safe filenames under the configured meetings folder.

- [x] **Step 4: Add unit tests**

Cover conversion, safe filename behavior, and state update behavior.

### Task 3: Notion Sync and Local API

**Files:**
- Create: `backend/src/notion_meeting_to_obsidian/notion.py`
- Create: `backend/src/notion_meeting_to_obsidian/sync.py`
- Create: `backend/src/notion_meeting_to_obsidian/api.py`
- Create: `backend/src/notion_meeting_to_obsidian/cli.py`

- [x] **Step 1: Implement official Notion API client**

Use the official REST API over HTTPS with `Authorization: Bearer`, `Notion-Version: 2022-06-28`, database query, page retrieval, and block children retrieval.

- [x] **Step 2: Implement incremental sync**

Compare Notion `last_edited_time` values with state and write only new or changed pages unless forced.

- [x] **Step 3: Implement FastAPI endpoints**

Expose health, sync, list notes, read note, save note, and draft page endpoints.

- [x] **Step 4: Implement CLI**

Expose `sync` and `serve` subcommands.

### Task 4: Angular Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/angular.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/app/app.component.ts`
- Create: `frontend/src/app/app.component.html`
- Create: `frontend/src/app/api.service.ts`

- [x] **Step 1: Create Angular shell**

Build a work-focused editor layout with sidebar, toolbar, editor, preview, and status regions.

- [x] **Step 2: Connect local API**

Use Angular `HttpClient` to call backend endpoints.

- [x] **Step 3: Add editing actions**

Allow sync, open note, edit Markdown, save note, and refresh vault list.

### Task 5: Verification

**Files:**
- Modify: `README.md`

- [x] **Step 1: Run backend tests**

Run `python -m pytest` from `backend`.

- [x] **Step 2: Verify repository state**

Initialize git in the final local repository, commit the scaffold, and report commands and any unavailable verification.

## Self-Review

- Spec coverage: Notion API, environment variables, Python CLI, FastAPI, Angular, Obsidian vault writes, edit-before-save, and edit-existing-notes are covered.
- Placeholder scan: no implementation placeholders remain.
- Type consistency: backend module names and frontend API paths are consistent across tasks.
