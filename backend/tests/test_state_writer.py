from pathlib import Path

from notion_meeting_to_obsidian.state import SyncState
from notion_meeting_to_obsidian.writer import safe_filename, write_markdown


def test_safe_filename_removes_windows_invalid_characters():
    assert safe_filename('Team: Planning / Q2?') == "Team- Planning - Q2-.md"


def test_state_tracks_incremental_sync(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state = SyncState.load(state_path)

    assert state.should_sync("page-1", "t1")

    state.mark_synced("page-1", "t1", tmp_path / "note.md")
    state.save()

    reloaded = SyncState.load(state_path)
    assert not reloaded.should_sync("page-1", "t1")
    assert reloaded.should_sync("page-1", "t2")


def test_write_markdown_creates_meetings_dir(tmp_path: Path):
    path = write_markdown(tmp_path / "Meetings", "Demo", "# Demo\n")

    assert path == tmp_path / "Meetings" / "Demo.md"
    assert path.read_text(encoding="utf-8") == "# Demo\n"
