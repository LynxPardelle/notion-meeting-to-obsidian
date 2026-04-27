from notion_meeting_to_obsidian.converter import page_to_markdown, rich_text_to_markdown


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
