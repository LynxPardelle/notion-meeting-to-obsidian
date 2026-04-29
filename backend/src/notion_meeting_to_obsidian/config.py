from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


@dataclass(frozen=True)
class Config:
    notion_token: str
    notion_source_id: str
    obsidian_vault_path: Path
    notion_source_ids: tuple[str, ...] = ()
    obsidian_meetings_folder: str = "Meetings"
    sync_state_path: Path | None = None
    sync_all_accessible: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        required = {
            "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
            "NOTION_SOURCE_ID": os.getenv("NOTION_SOURCE_ID"),
            "OBSIDIAN_VAULT_PATH": os.getenv("OBSIDIAN_VAULT_PATH"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigError("Missing environment variables: " + ", ".join(missing))

        state_path = os.getenv("SYNC_STATE_PATH")
        source_ids = tuple(
            source_id.strip()
            for source_id in os.getenv("NOTION_SOURCE_IDS", required["NOTION_SOURCE_ID"] or "").split(",")
            if source_id.strip()
        )
        return cls(
            notion_token=required["NOTION_TOKEN"] or "",
            notion_source_id=required["NOTION_SOURCE_ID"] or "",
            notion_source_ids=source_ids,
            obsidian_vault_path=Path(required["OBSIDIAN_VAULT_PATH"] or ""),
            obsidian_meetings_folder=os.getenv("OBSIDIAN_MEETINGS_FOLDER", "Meetings"),
            sync_state_path=Path(state_path) if state_path else None,
            sync_all_accessible=os.getenv("NOTION_SYNC_ALL_ACCESSIBLE", "").lower() in {"1", "true", "yes"},
        )

    @property
    def meetings_dir(self) -> Path:
        return self.obsidian_vault_path / self.obsidian_meetings_folder

    @property
    def state_path(self) -> Path:
        if self.sync_state_path:
            return self.sync_state_path
        return self.obsidian_vault_path / ".notion-meeting-sync" / "state.json"
