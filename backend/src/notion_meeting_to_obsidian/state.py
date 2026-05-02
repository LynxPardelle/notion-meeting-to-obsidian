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

    @classmethod
    def load(cls, path: Path) -> "SyncState":
        if not path.exists():
            return cls(path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(path=path, pages=data.get("pages", {}), active_page_ids=data.get("active_page_ids", []))

    def should_sync(self, page_id: str, last_edited_time: str, force: bool = False) -> bool:
        if force:
            return True
        previous = self.pages.get(page_id)
        return previous is None or previous.get("last_edited_time") != last_edited_time

    def mark_synced(self, page_id: str, last_edited_time: str, file_path: Path, title: str) -> None:
        self.pages[page_id] = {
            "last_edited_time": last_edited_time,
            "file_path": str(file_path),
            "title": title,
        }

    def mark_active(self, page_ids: list[str]) -> None:
        self.active_page_ids = page_ids

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"active_page_ids": self.active_page_ids, "pages": self.pages}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
