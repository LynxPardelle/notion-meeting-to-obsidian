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
    parent_id: str | None = None
    depth: int = 0


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
            parent_id = page_summary.get("_sync_parent_id")
            depth = page_summary.get("_sync_depth", 0)
            last_edited_time = page_summary.get("last_edited_time", "")
            title = extract_title(page_summary)
            previous_path = Path(state.pages.get(page_id, {}).get("file_path", ""))
            if not state.should_sync(page_id, last_edited_time, force=force):
                skipped.append(SyncedNote(page_id, title, previous_path, changed=False, parent_id=parent_id, depth=depth))
                continue

            page = self.notion.retrieve_page(page_id)
            blocks = self.notion.retrieve_block_children(page_id)
            markdown = page_to_markdown(page, blocks)
            subdir = self._subdir_for_page(page_summary)
            existing_path = state.pages.get(page_id, {}).get("file_path")
            if existing_path and subdir and Path(existing_path).parent == self.config.meetings_dir:
                existing_path = None
            file_path = write_markdown(
                self.config.meetings_dir,
                extract_title(page),
                markdown,
                subdir=subdir,
                existing_path=Path(existing_path) if existing_path else None,
                disambiguator=page_id[:8],
            )
            state.mark_synced(page_id, page.get("last_edited_time", last_edited_time), file_path)
            synced.append(SyncedNote(page_id, extract_title(page), file_path, changed=True, parent_id=parent_id, depth=depth))

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
            if exc.status not in {400, 404}:
                raise
        return self._page_tree(self.config.notion_source_id)

    def _page_tree(self, page_id: str) -> list[dict]:
        pages: list[dict] = []
        seen: set[str] = set()

        def visit(current_page_id: str, parent_id: str | None = None, ancestors: tuple[str, ...] = ()) -> None:
            if current_page_id in seen:
                return
            seen.add(current_page_id)
            page = self.notion.retrieve_page(current_page_id)
            page["_sync_parent_id"] = parent_id
            page["_sync_depth"] = len(ancestors)
            page["_sync_ancestor_titles"] = list(ancestors)
            pages.append(page)
            for block in self.notion.retrieve_block_children(current_page_id):
                if block.get("type") == "child_page":
                    visit(block["id"], current_page_id, ancestors + (extract_title(page),))

        visit(page_id)
        return pages

    def _subdir_for_page(self, page_summary: dict) -> Path | None:
        ancestor_titles = page_summary.get("_sync_ancestor_titles", [])
        if not ancestor_titles:
            return None
        parts = [title for title in ancestor_titles if title]
        return Path(*parts) if parts else None
