from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Config, ConfigError
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
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
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
        result = service.sync(force=force)
        return {
            "synced": [note.__dict__ | {"file_path": str(note.file_path)} for note in result.synced],
            "skipped": [note.__dict__ | {"file_path": str(note.file_path)} for note in result.skipped],
        }

    @app.get("/notes")
    def list_notes() -> list[dict[str, str]]:
        config = load_config()
        config.meetings_dir.mkdir(parents=True, exist_ok=True)
        notes = []
        for path in sorted(config.meetings_dir.glob("*.md")):
            notes.append({"name": path.stem, "path": str(path)})
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
        return {"page_id": payload.page_id, "markdown": service.draft_page(payload.page_id)}

    return app


app = create_app()
