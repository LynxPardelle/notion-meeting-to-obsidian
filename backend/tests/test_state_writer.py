from pathlib import Path

from notion_meeting_to_obsidian.state import SyncState
from notion_meeting_to_obsidian.writer import safe_filename, write_markdown


def test_safe_filename_removes_windows_invalid_characters():
    assert safe_filename('Team: Planning / Q2?') == "Team- Planning - Q2-.md"


def test_state_tracks_incremental_sync(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state = SyncState.load(state_path)

    assert state.should_sync("page-1", "t1")

    state.mark_synced("page-1", "t1", tmp_path / "note.md", "Note", metadata=[{"name": "Owner", "type": "people", "value": "Ana"}])
    state.save()

    reloaded = SyncState.load(state_path)
    assert not reloaded.should_sync("page-1", "t1")
    assert reloaded.should_sync("page-1", "t2")
    assert reloaded.pages["page-1"]["metadata"] == [{"name": "Owner", "type": "people", "value": "Ana"}]


def test_state_tracks_active_pages(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state = SyncState.load(state_path)

    state.mark_synced("page-1", "t1", tmp_path / "one.md", "One")
    state.mark_synced("old-page", "t1", tmp_path / "old.md", "Old")
    state.mark_active(["page-1"])
    state.save()

    reloaded = SyncState.load(state_path)
    assert reloaded.active_page_ids == ["page-1"]
    assert set(reloaded.pages) == {"page-1", "old-page"}


def test_write_markdown_creates_meetings_dir(tmp_path: Path):
    path = write_markdown(tmp_path / "Meetings", "Demo", "# Demo\n")

    assert path == tmp_path / "Meetings" / "Demo.md"
    assert path.read_text(encoding="utf-8") == "# Demo\n"


def test_write_markdown_disambiguates_new_file_when_title_exists(tmp_path: Path):
    first = write_markdown(tmp_path / "Meetings", "Demo", "# Demo\n")
    second = write_markdown(tmp_path / "Meetings", "Demo", "# Demo 2\n", disambiguator="page-2")

    assert first.name == "Demo.md"
    assert second.name == "Demo - page-2.md"


def test_write_markdown_writes_to_subdir(tmp_path: Path):
    path = write_markdown(tmp_path / "Meetings", "Child", "# Child\n", subdir=Path("Parent"))

    assert path == tmp_path / "Meetings" / "Parent" / "Child.md"
    assert path.read_text(encoding="utf-8") == "# Child\n"
