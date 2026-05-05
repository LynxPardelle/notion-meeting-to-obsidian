from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class SyncState:
    path: Path
    pages: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_page_ids: list[str] = field(default_factory=list)
    data_sources: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "SyncState":
        if not path.exists():
            return cls(path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            path=path,
            pages=data.get("pages", {}),
            active_page_ids=data.get("active_page_ids", []),
            data_sources=data.get("data_sources", {}),
        )

    def should_sync(self, page_id: str, last_edited_time: str, force: bool = False) -> bool:
        if force:
            return True
        previous = self.pages.get(page_id)
        return previous is None or previous.get("last_edited_time") != last_edited_time

    def mark_synced(
        self,
        page_id: str,
        last_edited_time: str,
        file_path: Path,
        title: str,
        notion_url: str = "",
        created_time: str = "",
        metadata: list[dict[str, str]] | None = None,
        parent_id: str | None = None,
        depth: int = 0,
        source_id: str = "",
        source_label: str = "",
    ) -> None:
        self.pages[page_id] = {
            "created_time": created_time,
            "depth": depth,
            "last_edited_time": last_edited_time,
            "file_path": str(file_path),
            "metadata": metadata or [],
            "notion_url": notion_url,
            "parent_id": parent_id,
            "source_id": source_id,
            "source_label": source_label,
            "title": title,
        }

    def mark_active(self, page_ids: list[str]) -> None:
        self.active_page_ids = page_ids

    def mark_data_sources(self, data_sources: list[dict[str, str]]) -> None:
        for data_source in data_sources:
            data_source_id = data_source.get("id", "")
            if not data_source_id:
                continue
            self.data_sources[data_source_id] = {
                "id": data_source_id,
                "name": data_source.get("name", "") or "Tabla de Notion",
            }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_page_ids": self.active_page_ids,
            "data_sources": self.data_sources,
            "pages": self.pages,
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
