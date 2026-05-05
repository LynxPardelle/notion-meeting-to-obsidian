from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Config, ConfigError
from .meeting_card import MeetingCard, MeetingTask, parse_meeting_card, update_meeting_card_sections
from .notion import NotionApiError
from .state import SyncState
from .sync import MeetingSyncService


class SaveNoteRequest(BaseModel):
    path: str
    markdown: str


class MeetingTaskPayload(BaseModel):
    text: str
    checked: bool = False


class MeetingCardPayload(BaseModel):
    summary: str = ""
    tasks: list[MeetingTaskPayload] = []
    notes: str = ""


class SaveMeetingCardRequest(BaseModel):
    path: str
    card: MeetingCardPayload


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

    def page_state_for_path(config: Config, note_path: Path) -> dict[str, Any]:
        state = SyncState.load(config.state_path)
        resolved = note_path.resolve()
        for page in state.pages.values():
            raw_path = page.get("file_path")
            if raw_path and Path(raw_path).resolve() == resolved:
                return page
        return {}

    def metadata_value(page_state: dict[str, Any], names: set[str]) -> str:
        normalized_names = {name.casefold() for name in names}
        for item in page_state.get("metadata", []):
            if str(item.get("name", "")).casefold() in normalized_names:
                return str(item.get("value", ""))
        return ""

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
        pages_by_path = {
            Path(page["file_path"]).resolve(): {"page_id": page_id, **page}
            for page_id, page in state.pages.items()
            if page.get("file_path")
        }
        pages_by_id = state.pages

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

        def parent_path_from_state(page_state: dict[str, Any]) -> str | None:
            parent_id = page_state.get("parent_id")
            if not parent_id:
                return None
            parts: list[str] = []
            seen: set[str] = set()
            while parent_id and parent_id not in seen:
                seen.add(parent_id)
                parent_state = pages_by_id.get(parent_id, {})
                title = str(parent_state.get("title", "")).strip()
                if title:
                    parts.append(title)
                parent_id = parent_state.get("parent_id")
            if not parts:
                return None
            return str(Path(*reversed(parts)))

        for path in sorted(config.meetings_dir.rglob("*.md"), key=note_sort_key):
            if active_paths and path.resolve() not in active_paths:
                continue
            relative = path.relative_to(config.meetings_dir)
            display_relative = display_relative_path(relative)
            page_state = pages_by_path.get(path.resolve(), {})
            parent = parent_path_from_state(page_state)
            has_synced_state = bool(page_state)
            notes.append(
                {
                    "created_time": page_state.get("created_time", ""),
                    "last_edited_time": page_state.get("last_edited_time", ""),
                    "metadata": page_state.get("metadata", []),
                    "name": path.stem,
                    "notion_url": page_state.get("notion_url", ""),
                    "path": str(path),
                    "relative_path": str(display_relative),
                    "depth": page_state.get("depth", len(display_relative.parts) - 1),
                    "parent": parent
                    or (
                        None
                        if has_synced_state
                        else str(display_relative.parent)
                        if display_relative.parent != Path(".")
                        else None
                    ),
                    "parent_id": page_state.get("parent_id"),
                    "source_id": page_state.get("source_id", ""),
                    "source_label": str(page_state.get("source_label", "")).strip(),
                }
            )
        return notes

    @app.get("/notes/read")
    def read_note(path: str) -> dict[str, Any]:
        config = load_config()
        note_path = safe_note_path(config, path)
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="Note not found.")
        markdown = note_path.read_text(encoding="utf-8")
        card = parse_meeting_card(markdown)
        page_state = page_state_for_path(config, note_path)
        summary = card.summary or metadata_value(page_state, {"Summary", "Resumen"})
        return {
            "path": str(note_path),
            "markdown": markdown,
            "card": {
                "summary": summary,
                "tasks": [task.__dict__ for task in card.tasks],
                "notes": card.notes,
            },
        }

    @app.post("/notes/save")
    def save_note(payload: SaveNoteRequest) -> dict[str, str]:
        config = load_config()
        note_path = safe_note_path(config, payload.path)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(payload.markdown, encoding="utf-8", newline="\n")
        return {"path": str(note_path), "status": "saved"}

    @app.post("/notes/card/save")
    def save_note_card(payload: SaveMeetingCardRequest) -> dict[str, str]:
        config = load_config()
        note_path = safe_note_path(config, payload.path)
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="Note not found.")
        markdown = note_path.read_text(encoding="utf-8")
        card = MeetingCard(
            summary=payload.card.summary,
            tasks=[MeetingTask(text=task.text, checked=task.checked) for task in payload.card.tasks],
            notes=payload.card.notes,
        )
        note_path.write_text(update_meeting_card_sections(markdown, card), encoding="utf-8", newline="\n")
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
