from notion_meeting_to_obsidian.metadata import notion_properties_to_metadata


def test_notion_properties_to_metadata_formats_common_database_values():
    properties = {
        "Name": {
            "type": "title",
            "title": [{"plain_text": "Sprint Planning"}],
        },
        "Owner": {
            "type": "people",
            "people": [{"name": "Ana"}, {"name": "Luis"}],
        },
        "Date": {
            "type": "date",
            "date": {"start": "2026-05-02", "end": None},
        },
        "Status": {
            "type": "select",
            "select": {"name": "Nueva"},
        },
        "Tags": {
            "type": "multi_select",
            "multi_select": [{"name": "AI"}, {"name": "Backend"}],
        },
        "Empty": {
            "type": "rich_text",
            "rich_text": [],
        },
    }

    metadata = notion_properties_to_metadata(properties)

    assert metadata == [
        {"name": "Owner", "type": "people", "value": "Ana, Luis"},
        {"name": "Date", "type": "date", "value": "2026-05-02"},
        {"name": "Status", "type": "select", "value": "Nueva"},
        {"name": "Tags", "type": "multi_select", "value": "AI, Backend"},
    ]
