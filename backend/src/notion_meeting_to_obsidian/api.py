from __future__ import annotations

import os
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


def cors_origins() -> list[str]:
    ports = {"4200", "47863", os.getenv("FRONTEND_PORT", "").strip()}
    origins = {
        f"http://localhost:{port}"
        for port in ports
        if port
    } | {
        f"http://127.0.0.1:{port}"
        for port in ports
        if port
    }
    origins.update(
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    )
    return sorted(origins)


def create_app() -> FastAPI:
    app = FastAPI(title="Notion Meeting to Obsidian")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
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

    def metadata_value_by_name(page_state: dict[str, Any], name: str | None) -> str:
        if not name:
            return ""
        normalized_name = name.casefold()
        for item in page_state.get("metadata", []):
            if str(item.get("name", "")).casefold() == normalized_name:
                return str(item.get("value", ""))
        return ""

    def source_schemas(state: SyncState) -> list[dict[str, Any]]:
        pages_by_source: dict[str, list[dict[str, Any]]] = {}
        for page_id, page in state.pages.items():
            if state.active_page_ids and page_id not in state.active_page_ids:
                continue
            source_id = str(page.get("source_id", ""))
            if not source_id:
                continue
            pages_by_source.setdefault(source_id, []).append(page)

        source_ids = set(state.data_sources) | set(pages_by_source)
        schemas: list[dict[str, Any]] = []
        for source_id in source_ids:
            source = state.data_sources.get(source_id, {})
            pages = pages_by_source.get(source_id, [])
            properties = source_properties(pages)
            schemas.append(
                {
                    "id": source_id,
                    "name": str(source.get("name") or source_label_from_pages(pages) or "Tabla de Notion").strip(),
                    "note_count": len(pages),
                    "properties": properties,
                    "mapping": suggested_mapping(properties),
                }
            )
        return sorted(schemas, key=lambda source: str(source["name"]).casefold())

    def source_label_from_pages(pages: list[dict[str, Any]]) -> str:
        for page in pages:
            label = str(page.get("source_label", "")).strip()
            if label:
                return label
        return ""

    def source_properties(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_name: dict[str, dict[str, Any]] = {}
        for page in pages:
            for item in page.get("metadata", []):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                current = by_name.setdefault(
                    name,
                    {"name": name, "type": str(item.get("type", "")), "usage_count": 0, "sample": ""},
                )
                current["usage_count"] += 1
                value = str(item.get("value", "")).strip()
                if value and not current["sample"]:
                    current["sample"] = value
        return sorted(by_name.values(), key=lambda item: str(item["name"]).casefold())

    def suggested_mapping(properties: list[dict[str, Any]]) -> dict[str, str | None]:
        return {
            "date": mapped_property(properties, {"fecha", "date", "meeting date"}, {"date"}),
            "notes": mapped_property(
                properties, {"notas", "notes", "texto", "transcript", "contenido"}, {"rich_text"}, fallback_by_type=False
            ),
            "people": mapped_property(properties, {"personas", "people", "texto", "owner", "assignee"}, {"people"}),
            "status": mapped_property(properties, {"estado", "status"}, {"status", "select"}),
            "summary": mapped_property(properties, {"summary", "resumen"}, {"rich_text"}),
            "tasks": mapped_property(
                properties, {"tareas", "tasks", "action items", "acciones"}, {"rich_text"}, fallback_by_type=False
            ),
        }

    def mapped_property(
        properties: list[dict[str, Any]], names: set[str], types: set[str], fallback_by_type: bool = True
    ) -> str | None:
        normalized_names = {name.casefold() for name in names}
        for item in properties:
            if str(item.get("name", "")).casefold() in normalized_names and str(item.get("type", "")) in types:
                return str(item["name"])
        if not fallback_by_type:
            return None
        for item in properties:
            if str(item.get("type", "")) in types:
                return str(item["name"])
        return None

    def mapped_card(card: MeetingCard, page_state: dict[str, Any], state: SyncState) -> MeetingCard:
        source_id = str(page_state.get("source_id", ""))
        schema = next((item for item in source_schemas(state) if item["id"] == source_id), None)
        mapping = schema.get("mapping", {}) if schema else {}
        summary = card.summary or metadata_value_by_name(page_state, mapping.get("summary")) or metadata_value(
            page_state, {"Summary", "Resumen"}
        )
        notes = card.notes or metadata_value_by_name(page_state, mapping.get("notes"))
        tasks = card.tasks or parse_mapped_tasks(metadata_value_by_name(page_state, mapping.get("tasks")))
        return MeetingCard(summary=summary, tasks=tasks, notes=notes)

    def parse_mapped_tasks(raw: str) -> list[MeetingTask]:
        if not raw.strip():
            return []
        parsed = parse_meeting_card(f"# Tareas\n\n## Tareas\n\n{raw.strip()}\n")
        return parsed.tasks

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

    @app.get("/note-sources")
    def list_note_sources() -> list[dict[str, Any]]:
        config = load_config()
        state = SyncState.load(config.state_path)
        counts: dict[str, int] = {}
        for page_id, page in state.pages.items():
            if state.active_page_ids and page_id not in state.active_page_ids:
                continue
            source_id = str(page.get("source_id", ""))
            if not source_id:
                continue
            counts[source_id] = counts.get(source_id, 0) + 1
        sources = [
            {
                "id": source_id,
                "name": str(source.get("name", "")).strip() or "Tabla de Notion",
                "note_count": counts.get(source_id, 0),
            }
            for source_id, source in state.data_sources.items()
        ]
        for source_id, count in counts.items():
            if source_id not in state.data_sources:
                sources.append({"id": source_id, "name": "Tabla de Notion", "note_count": count})
        return sorted(sources, key=lambda source: str(source["name"]).casefold())

    @app.get("/note-sources/schema")
    def list_note_source_schema() -> list[dict[str, Any]]:
        config = load_config()
        state = SyncState.load(config.state_path)
        return source_schemas(state)

    @app.get("/notes/read")
    def read_note(path: str) -> dict[str, Any]:
        config = load_config()
        note_path = safe_note_path(config, path)
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="Note not found.")
        markdown = note_path.read_text(encoding="utf-8")
        card = parse_meeting_card(markdown)
        page_state = page_state_for_path(config, note_path)
        card = mapped_card(card, page_state, SyncState.load(config.state_path))
        return {
            "path": str(note_path),
            "markdown": markdown,
            "card": {
                "summary": card.summary,
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
