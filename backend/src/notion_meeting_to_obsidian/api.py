from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Config, ConfigError
from .notion import NotionApiError
from .state import SyncState
from .sync import MeetingSyncService


class SaveNoteRequest(BaseModel):
    path: str
    markdown: str


class DraftRequest(BaseModel):
    page_id: str


def create_app() -> FastAPI:
    app = FastAPI(title="Notion Meeting to Obsidian")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "http://127.0.0.1:4200",
            "http://localhost:47863",
            "http://127.0.0.1:47863",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def load_config() -> Config:
        try:
            return Config.from_env()
        except ConfigError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def safe_note_path(config: Config, raw_path: str) -> Path:
        base = config.meetings_dir.resolve()
        candidate = (base / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        if base not in candidate.parents and candidate != base:
            raise HTTPException(status_code=400, detail="Path is outside the configured meetings folder.")
        return candidate

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/sync")
    def sync(force: bool = False) -> dict[str, Any]:
        service = MeetingSyncService(load_config())
        try:
            result = service.sync(force=force)
        except NotionApiError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {
            "synced": [note.__dict__ | {"file_path": str(note.file_path)} for note in result.synced],
            "skipped": [note.__dict__ | {"file_path": str(note.file_path)} for note in result.skipped],
            "deleted": [str(path) for path in result.deleted or []],
        }

    @app.get("/notes")
    def list_notes() -> list[dict[str, Any]]:
        config = load_config()
        config.meetings_dir.mkdir(parents=True, exist_ok=True)
        state = SyncState.load(config.state_path)
        active_paths = {
            Path(page["file_path"]).resolve()
            for page_id, page in state.pages.items()
            if not state.active_page_ids or page_id in state.active_page_ids
        }
        notes = []
        def note_sort_key(path: Path) -> tuple[str, int, str]:
            relative = display_relative_path(path.relative_to(config.meetings_dir))
            root_name = relative.parts[0]
            root_stem = Path(root_name).stem
            return (root_stem.casefold(), len(relative.parts), str(relative).casefold())

        def display_relative_path(relative: Path) -> Path:
            parts = list(relative.parts)
            if len(parts) >= 2 and Path(parts[-1]).stem == parts[-2]:
                return Path(*parts[:-2], parts[-1]) if len(parts) > 2 else Path(parts[-1])
            return relative

        for path in sorted(config.meetings_dir.rglob("*.md"), key=note_sort_key):
            if active_paths and path.resolve() not in active_paths:
                continue
            relative = path.relative_to(config.meetings_dir)
            display_relative = display_relative_path(relative)
            notes.append(
                {
                    "name": path.stem,
                    "path": str(path),
                    "relative_path": str(display_relative),
                    "depth": len(display_relative.parts) - 1,
                    "parent": str(display_relative.parent) if display_relative.parent != Path(".") else None,
                }
            )
        return notes

    @app.get("/notes/read")
    def read_note(path: str) -> dict[str, str]:
        config = load_config()
        note_path = safe_note_path(config, path)
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="Note not found.")
        return {"path": str(note_path), "markdown": note_path.read_text(encoding="utf-8")}

    @app.post("/notes/save")
    def save_note(payload: SaveNoteRequest) -> dict[str, str]:
        config = load_config()
        note_path = safe_note_path(config, payload.path)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(payload.markdown, encoding="utf-8", newline="\n")
        return {"path": str(note_path), "status": "saved"}

    @app.post("/draft")
    def draft(payload: DraftRequest) -> dict[str, str]:
        service = MeetingSyncService(load_config())
        try:
            markdown = service.draft_page(payload.page_id)
        except NotionApiError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"page_id": payload.page_id, "markdown": markdown}

    return app


app = create_app()
