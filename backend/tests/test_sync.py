from pathlib import Path

from notion_meeting_to_obsidian.config import Config
from notion_meeting_to_obsidian.notion import NotionApiError
from notion_meeting_to_obsidian.sync import MeetingSyncService


class PageOnlyNotion:
    def query_database(self, source_id: str):
        raise NotionApiError("not found", status=404)

    def retrieve_page(self, page_id: str):
        title = "Single Meeting" if page_id == "page-1" else page_id
        return {
            "id": page_id,
            "url": "https://notion.so/page",
            "last_edited_time": "2026-04-28T00:00:00.000Z",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": title, "annotations": {}}],
                }
            },
        }

    def retrieve_block_children(self, block_id: str):
        return [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": "Notes", "annotations": {}}]},
            }
        ]

    def retrieve_block_children_recursive(self, block_id: str):
        return self.retrieve_block_children(block_id)


def test_sync_accepts_page_source_when_database_is_not_found(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="page-1",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
    )

    result = MeetingSyncService(config, notion=PageOnlyNotion()).sync()

    assert len(result.synced) == 1
    assert result.synced[0].title == "Single Meeting"
    assert (tmp_path / "Meetings" / "Single Meeting.md").exists()


def test_sync_accepts_page_source_when_notion_reports_page_not_database(tmp_path: Path):
    notion = PageOnlyNotion()

    def query_database(source_id: str):
        raise NotionApiError("Provided ID is a page, not a database", status=400)

    notion.query_database = query_database
    config = Config(
        notion_token="secret",
        notion_source_id="page-1",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
    )

    result = MeetingSyncService(config, notion=notion).sync(force=True)

    assert len(result.synced) == 1
    assert (tmp_path / "Meetings" / "Single Meeting.md").exists()


class ParentPageWithChildrenNotion(PageOnlyNotion):
    def retrieve_page(self, page_id: str):
        titles = {
            "parent": "Root Meeting",
            "child-1": "Follow-up Notes",
            "child-2": "Follow-up Notes",
            "grandchild": "Action Items",
        }
        return {
            "id": page_id,
            "url": f"https://notion.so/{page_id}",
            "last_edited_time": f"2026-04-28T00:00:0{len(page_id)}.000Z",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": titles[page_id], "annotations": {}}],
                }
            },
        }

    def retrieve_block_children(self, block_id: str):
        if block_id == "parent":
            return [
                {"id": "child-1", "type": "child_page", "child_page": {"title": "Follow-up Notes"}},
                {"id": "child-2", "type": "child_page", "child_page": {"title": "Follow-up Notes"}},
            ]
        if block_id == "child-1":
            return [
                {"id": "grandchild", "type": "child_page", "child_page": {"title": "Action Items"}},
            ]
        return [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": f"Body for {block_id}", "annotations": {}}]},
            }
        ]

    def search_pages(self):
        return [
            {"id": "parent", "parent": {"type": "workspace", "workspace": True}},
            {"id": "child-1", "parent": {"type": "page_id", "page_id": "parent"}},
            {"id": "child-2", "parent": {"type": "page_id", "page_id": "parent"}},
        ]


def test_sync_page_source_recursively_syncs_child_pages_and_disambiguates_duplicate_titles(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="parent",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
    )

    result = MeetingSyncService(config, notion=ParentPageWithChildrenNotion()).sync(force=True)

    assert [note.page_id for note in result.synced] == ["parent", "child-1", "grandchild", "child-2"]
    assert (tmp_path / "Meetings" / "Root Meeting" / "Root Meeting.md").exists()
    assert (tmp_path / "Meetings" / "Root Meeting" / "Follow-up Notes" / "Follow-up Notes.md").exists()
    assert (tmp_path / "Meetings" / "Root Meeting" / "Follow-up Notes - child-2.md").exists()
    assert (tmp_path / "Meetings" / "Root Meeting" / "Follow-up Notes" / "Action Items.md").exists()


def test_sync_all_accessible_pages_uses_visible_roots_and_preserves_hierarchy(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="unused-when-sync-all-is-enabled",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
        sync_all_accessible=True,
    )

    result = MeetingSyncService(config, notion=ParentPageWithChildrenNotion()).sync(force=True)

    assert [note.page_id for note in result.synced] == ["parent", "child-1", "grandchild", "child-2"]
    assert result.synced[1].parent_id == "parent"
    assert result.synced[1].depth == 1


def test_sync_accepts_multiple_selected_page_sources(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="page-1",
        notion_source_ids=("page-1", "page-2"),
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
    )

    result = MeetingSyncService(config, notion=PageOnlyNotion()).sync(force=True)

    assert [note.page_id for note in result.synced] == ["page-1", "page-2"]
    assert (tmp_path / "Meetings" / "Single Meeting.md").exists()
    assert (tmp_path / "Meetings" / "page-2.md").exists()


def test_sync_deletes_stale_synced_notes_when_enabled(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="page-1",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
        delete_stale_synced_notes=True,
    )
    meetings_dir = tmp_path / "Meetings"
    stale = meetings_dir / "Old Parent" / "Old Child.md"
    stale_root = meetings_dir / "Unrelated Root.md"
    orphan_generated = meetings_dir / "Old Generated.md"
    duplicate_active = meetings_dir / "Duplicate Active.md"
    manual_note = meetings_dir / "Manual Note.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("# Old Child\n", encoding="utf-8")
    stale_root.write_text("# Unrelated Root\n", encoding="utf-8")
    orphan_generated.write_text('---\nnotion_id: "old-orphan"\n---\n# Old Generated\n', encoding="utf-8")
    duplicate_active.write_text('---\nnotion_id: "page-1"\n---\n# Duplicate Active\n', encoding="utf-8")
    manual_note.write_text("# Manual Note\n", encoding="utf-8")
    state_path = tmp_path / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"pages":{'
        '"page-1":{"file_path":"' + (meetings_dir / "Single Meeting.md").as_posix() + '","last_edited_time":"old"},'
        '"old-page":{"file_path":"' + stale.as_posix() + '","last_edited_time":"old"},'
        '"unrelated-root":{"file_path":"' + stale_root.as_posix() + '","last_edited_time":"old"}'
        "}}",
        encoding="utf-8",
    )

    result = MeetingSyncService(config, notion=PageOnlyNotion()).sync(force=True)

    assert set(result.deleted) == {stale, stale_root, orphan_generated, duplicate_active, manual_note}
    assert not stale.exists()
    assert not stale.parent.exists()
    assert not stale_root.exists()
    assert not orphan_generated.exists()
    assert not duplicate_active.exists()
    assert not manual_note.exists()
    assert (meetings_dir / "Single Meeting.md").exists()


def test_sync_deletes_previous_file_when_note_moves_under_parent(tmp_path: Path):
    config = Config(
        notion_token="secret",
        notion_source_id="parent",
        obsidian_vault_path=tmp_path,
        obsidian_meetings_folder="Meetings",
    )
    meetings_dir = tmp_path / "Meetings"
    previous_child_path = meetings_dir / "Follow-up Notes.md"
    previous_child_path.parent.mkdir(parents=True)
    previous_child_path.write_text("# Follow-up Notes\n", encoding="utf-8")
    state_path = tmp_path / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"pages":{'
        '"child-1":{"file_path":"' + previous_child_path.as_posix() + '","last_edited_time":"old"}'
        "}}",
        encoding="utf-8",
    )

    result = MeetingSyncService(config, notion=ParentPageWithChildrenNotion()).sync(force=True)

    assert previous_child_path in result.deleted
    assert not previous_child_path.exists()
    assert (meetings_dir / "Root Meeting" / "Follow-up Notes" / "Follow-up Notes.md").exists()
