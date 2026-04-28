from pathlib import Path

from notion_meeting_to_obsidian.config import Config
from notion_meeting_to_obsidian.notion import NotionApiError
from notion_meeting_to_obsidian.sync import MeetingSyncService


class PageOnlyNotion:
    def query_database(self, source_id: str):
        raise NotionApiError("not found", status=404)

    def retrieve_page(self, page_id: str):
        return {
            "id": page_id,
            "url": "https://notion.so/page",
            "last_edited_time": "2026-04-28T00:00:00.000Z",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Single Meeting", "annotations": {}}],
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
