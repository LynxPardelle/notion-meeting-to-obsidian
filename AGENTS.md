# Codex Instructions

## Repository Workflow
- At the start of every Codex work session in this repository, run `git pull --rebase --autostash` before making changes.
- At the end of a work session, summarize the changes and ask for explicit permission before pushing to the remote repository.
- Do not push without the user's approval.

## Accuracy And Safety
- Do not guess or invent details. If a command, tool, or source fails, report the exact failure.
- Do not print secrets from `.env` or other local secret files.
- Proactively flag security concerns introduced by a requested change.

## Local Runtime
- The Docker frontend should not use port `4200`; this project currently publishes it on `127.0.0.1:47863`.
- The backend publishes on `127.0.0.1:8765`.
