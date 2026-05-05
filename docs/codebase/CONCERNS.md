# Concerns

## Current Risks

### Python 3.14 Deprecation Warnings

The backend test suite passes, but local Python 3.14 emits deprecation warnings from FastAPI/Starlette internals around `asyncio.iscoroutinefunction`. This is not currently blocking. Docker uses Python 3.12.

### Frontend Component Size

`frontend/src/app/app.component.ts`, `frontend/src/app/app.component.html`, and `frontend/src/styles.css` are high-churn files. Future UI growth may benefit from splitting the app into smaller Angular components and style sections.

### Sync Complexity

`backend/src/notion_meeting_to_obsidian/sync.py` is the highest-churn backend file and owns hierarchy traversal, delta decisions, writing, deletion, and state updates. Changes here should be test-first.

### No CI/CD Pipeline

No CI/CD configuration is present. Contributors must run tests/build locally unless CI is added later.

### No Dedicated Frontend Unit Tests

The frontend build is verified, but no visible Angular component/unit specs are present. UI behavior currently relies on manual verification and TypeScript build checks.

### Local Secrets

`.env` contains Notion tokens and machine-specific vault paths. It is ignored by Git. Contributors must keep real secrets out of commits.

## Recommended Follow-Ups

- Add CI for backend tests and frontend build.
- Add frontend tests for source-tree rendering, theme toggle, meeting-card save, and schema mapping display.
- Consider splitting `AppComponent` after the next major UI feature.
- Keep Python local development aligned with Docker Python 3.12 if warning noise becomes distracting.

## Evidence

- `backend/Dockerfile`
- `backend/tests/test_sync.py`
- `frontend/src/app/app.component.ts`
- `frontend/src/app/app.component.html`
- `frontend/src/styles.css`
- `.gitignore`
- `git log --oneline --decorate --graph --all`
