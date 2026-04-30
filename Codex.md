# Development Memory

## Codex Workflow
- Start every Codex session in this repository by running:

```powershell
git pull --rebase --autostash
```

- Before ending a completed work session, ask the user for permission before pushing changes to the remote repository.
- Do not push without explicit user approval.

## Current Local Setup
- Docker Compose runs the backend on `http://127.0.0.1:8765`.
- Docker Compose runs the frontend on `http://127.0.0.1:47863`.
- Port `4200` is intentionally avoided because it is Angular's common default dev port.
- The local `.env` file is ignored by Git and contains machine-specific values and secrets.
