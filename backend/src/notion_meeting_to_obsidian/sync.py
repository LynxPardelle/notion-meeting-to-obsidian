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
    deleted: list[Path] | None = None


class MeetingSyncService:
    def __init__(self, config: Config, notion: NotionClient | None = None) -> None:
        self.config = config
        self.notion = notion or NotionClient(config.notion_token)

    def sync(self, force: bool = False) -> SyncResult:
        state = SyncState.load(self.config.state_path)
        synced: list[SyncedNote] = []
        skipped: list[SyncedNote] = []
        deleted: list[Path] = []

        pages = self._source_pages()
        active_page_ids: list[str] = []
        for page_summary in pages:
            page_id = page_summary["id"]
            active_page_ids.append(page_id)
            parent_id = page_summary.get("_sync_parent_id")
            depth = page_summary.get("_sync_depth", 0)
            last_edited_time = page_summary.get("last_edited_time", "")
            title = extract_title(page_summary)
            previous_path = Path(state.pages.get(page_id, {}).get("file_path", ""))
            if not state.should_sync(page_id, last_edited_time, force=force):
                skipped.append(SyncedNote(page_id, title, previous_path, changed=False, parent_id=parent_id, depth=depth))
                continue

            page = self.notion.retrieve_page(page_id)
            blocks = self.notion.retrieve_block_children_recursive(page_id)
            markdown = page_to_markdown(page, blocks)
            subdir = self._subdir_for_page(page_summary)
            previous_raw_path = state.pages.get(page_id, {}).get("file_path")
            existing_path = previous_raw_path
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
            deleted.extend(self._delete_replaced_file(previous_raw_path, file_path))
            state.mark_synced(page_id, page.get("last_edited_time", last_edited_time), file_path)
            synced.append(SyncedNote(page_id, extract_title(page), file_path, changed=True, parent_id=parent_id, depth=depth))

        if self.config.delete_stale_synced_notes:
            deleted.extend(self._delete_stale_files(state, active_page_ids))
            deleted.extend(self._delete_unlisted_meeting_files(state, active_page_ids))
        state.mark_active(active_page_ids)
        state.save()
        return SyncResult(synced=synced, skipped=skipped, deleted=deleted)

    def draft_page(self, page_id: str) -> str:
        page = self.notion.retrieve_page(page_id)
        blocks = self.notion.retrieve_block_children_recursive(page_id)
        return page_to_markdown(page, blocks)

    def _source_pages(self) -> list[dict]:
        if self.config.sync_all_accessible:
            return self._all_accessible_page_trees()

        pages: list[dict] = []
        seen: set[str] = set()
        for source_id in self.config.notion_source_ids or (self.config.notion_source_id,):
            try:
                pages.extend(self.notion.query_database(source_id))
            except NotionApiError as exc:
                if exc.status not in {400, 404}:
                    raise
                pages.extend(self._page_tree(source_id, seen=seen))
        return pages

    def _all_accessible_page_trees(self) -> list[dict]:
        visible_pages = self.notion.search_pages()
        visible_ids = {page["id"] for page in visible_pages}
        root_ids: list[str] = []
        for page in visible_pages:
            parent = page.get("parent", {})
            parent_page_id = parent.get("page_id") if parent.get("type") == "page_id" else None
            if parent_page_id not in visible_ids:
                root_ids.append(page["id"])

        pages: list[dict] = []
        seen: set[str] = set()
        for root_id in root_ids:
            pages.extend(self._page_tree(root_id, seen=seen))
        return pages

    def _page_tree(self, page_id: str, seen: set[str] | None = None) -> list[dict]:
        pages: list[dict] = []
        visited = seen if seen is not None else set()

        def visit(current_page_id: str, parent_id: str | None = None, ancestors: tuple[str, ...] = ()) -> None:
            if current_page_id in visited:
                return
            visited.add(current_page_id)
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

    def _delete_stale_files(self, state: SyncState, active_page_ids: list[str]) -> list[Path]:
        active = set(active_page_ids)
        deleted: list[Path] = []
        for page_id, page in list(state.pages.items()):
            if page_id in active:
                continue
            raw_path = page.get("file_path")
            if not raw_path:
                continue
            file_path = Path(raw_path)
            if self._is_safe_meeting_file(file_path) and file_path.exists():
                file_path.unlink()
                deleted.append(file_path)
                self._remove_empty_parent_dirs(file_path.parent)
            state.pages.pop(page_id, None)
        return deleted

    def _delete_replaced_file(self, previous_raw_path: str | None, current_path: Path) -> list[Path]:
        if not previous_raw_path:
            return []
        previous_path = Path(previous_raw_path)
        try:
            if previous_path.resolve() == current_path.resolve():
                return []
        except OSError:
            return []
        if not self._is_safe_meeting_file(previous_path) or not previous_path.exists():
            return []
        previous_path.unlink()
        self._remove_empty_parent_dirs(previous_path.parent)
        return [previous_path]

    def _delete_unlisted_meeting_files(self, state: SyncState, active_page_ids: list[str]) -> list[Path]:
        active = set(active_page_ids)
        protected_paths = {
            Path(page["file_path"]).resolve()
            for page_id, page in state.pages.items()
            if page_id in active and page.get("file_path")
        }
        deleted: list[Path] = []
        for file_path in self.config.meetings_dir.rglob("*.md"):
            resolved = file_path.resolve()
            if resolved in protected_paths:
                continue
            file_path.unlink()
            deleted.append(file_path)
            self._remove_empty_parent_dirs(file_path.parent)
        return deleted

    def _is_safe_meeting_file(self, file_path: Path) -> bool:
        try:
            resolved = file_path.resolve()
            meetings_dir = self.config.meetings_dir.resolve()
        except OSError:
            return False
        return resolved.suffix == ".md" and meetings_dir in resolved.parents

    def _remove_empty_parent_dirs(self, start_dir: Path) -> None:
        meetings_dir = self.config.meetings_dir.resolve()
        current = start_dir.resolve()
        while current != meetings_dir and meetings_dir in current.parents:
            try:
                current.rmdir()
            except OSError:
                return
            current = current.parent
