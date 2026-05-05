from notion_meeting_to_obsidian.converter import extract_title, page_to_markdown, rich_text_to_markdown


def test_rich_text_to_markdown_preserves_annotations_and_links():
    result = rich_text_to_markdown(
        [
            {
                "plain_text": "Docs",
                "href": "https://example.com",
                "annotations": {"bold": True},
            }
        ]
    )

    assert result == "[**Docs**](https://example.com)"


def test_page_to_markdown_generates_frontmatter_and_blocks():
    page = {
        "id": "page-1",
        "url": "https://notion.so/page-1",
        "last_edited_time": "2026-04-27T10:00:00.000Z",
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "Weekly Sync", "annotations": {}}],
            }
        },
    }
    blocks = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"plain_text": "Action items", "annotations": {}}]},
        },
        {
            "type": "to_do",
            "to_do": {
                "checked": False,
                "rich_text": [{"plain_text": "Send recap", "annotations": {}}],
            },
        },
    ]

    markdown = page_to_markdown(page, blocks)

    assert 'title: "Weekly Sync"' in markdown
    assert 'notion_id: "page-1"' in markdown
    assert "# Weekly Sync" in markdown
    assert "## Action items" in markdown
    assert "- [ ] Send recap" in markdown


def test_extract_title_uses_plain_text_without_markdown_annotations():
    page = {
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "2026-04-28T15:06", "annotations": {"bold": True}}],
            }
        }
    }

    assert extract_title(page) == "2026-04-28T15:06"


def test_page_to_markdown_renders_nested_transcription_children():
    page = {
        "id": "meeting",
        "url": "https://notion.so/meeting",
        "last_edited_time": "2026-04-28T10:00:00.000Z",
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "Today 15:06", "annotations": {}}],
            }
        },
    }
    blocks = [
        {
            "id": "transcription",
            "type": "transcription",
            "has_children": True,
            "transcription": {},
            "_children": [
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": []},
                    "_children": [
                        {
                            "type": "heading_3",
                            "heading_3": {"rich_text": [{"plain_text": "Action items", "annotations": {}}]},
                        },
                        {
                            "type": "to_do",
                            "to_do": {
                                "checked": False,
                                "rich_text": [{"plain_text": "Review QA", "annotations": {}}],
                            },
                        },
                    ],
                }
            ],
        }
    ]

    markdown = page_to_markdown(page, blocks)

    assert "### Action items" in markdown
    assert "- [ ] Review QA" in markdown
    assert "    - [ ] Review QA" not in markdown


def test_page_to_markdown_renders_child_database_reference():
    page = {
        "id": "page-1",
        "url": "https://notion.so/page-1",
        "last_edited_time": "2026-04-28T10:00:00.000Z",
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "Meeting", "annotations": {}}],
            }
        },
    }
    blocks = [{"id": "db-1", "type": "child_database", "child_database": {"title": "Tabla"}}]

    markdown = page_to_markdown(page, blocks)

    assert "**Database:** Tabla" in markdown
