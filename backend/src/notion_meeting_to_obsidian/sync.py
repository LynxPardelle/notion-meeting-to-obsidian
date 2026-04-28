from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .converter import extract_title, page_to_markdown
from .notion import NotionApiError, NotionClient
from .state import SyncState
from .writer import write_markdown


@dataclass(frozen=True)
class SyncedNote:
    page_id: str
    title: str
    file_path: Path
    changed: bool


@dataclass(frozen=True)
class SyncResult:
    synced: list[SyncedNote]
    skipped: list[SyncedNote]


class MeetingSyncService:
    def __init__(self, config: Config, notion: NotionClient | None = None) -> None:
        self.config = config
        self.notion = notion or NotionClient(config.notion_token)

    def sync(self, force: bool = False) -> SyncResult:
        state = SyncState.load(self.config.state_path)
        synced: list[SyncedNote] = []
        skipped: list[SyncedNote] = []

        pages = self._source_pages()
        for page_summary in pages:
            page_id = page_summary["id"]
            last_edited_time = page_summary.get("last_edited_time", "")
            title = extract_title(page_summary)
            previous_path = Path(state.pages.get(page_id, {}).get("file_path", ""))
            if not state.should_sync(page_id, last_edited_time, force=force):
                skipped.append(SyncedNote(page_id, title, previous_path, changed=False))
                continue

            page = self.notion.retrieve_page(page_id)
            blocks = self.notion.retrieve_block_children(page_id)
            markdown = page_to_markdown(page, blocks)
            file_path = write_markdown(self.config.meetings_dir, extract_title(page), markdown)
            state.mark_synced(page_id, page.get("last_edited_time", last_edited_time), file_path)
            synced.append(SyncedNote(page_id, extract_title(page), file_path, changed=True))

        state.save()
        return SyncResult(synced=synced, skipped=skipped)

    def draft_page(self, page_id: str) -> str:
        page = self.notion.retrieve_page(page_id)
        blocks = self.notion.retrieve_block_children(page_id)
        return page_to_markdown(page, blocks)

    def _source_pages(self) -> list[dict]:
        try:
            return self.notion.query_database(self.config.notion_source_id)
        except NotionApiError as exc:
            if exc.status != 404:
                raise
        return [self.notion.retrieve_page(self.config.notion_source_id)]
