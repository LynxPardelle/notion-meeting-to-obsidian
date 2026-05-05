from notion_meeting_to_obsidian.notion import NotionApiError, NotionClient


class MultipleDataSourceNotion(NotionClient):
    def __init__(self):
        super().__init__("secret")
        self.queries: list[tuple[str, str | None]] = []

    def _request(self, method, path, payload=None, notion_version=None):
        self.queries.append((path, notion_version))
        if path == "/databases/database-id/query":
            raise NotionApiError(
                "Notion API error 400",
                status=400,
                detail={
                    "additional_data": {
                        "error_type": "multiple_data_sources_for_database",
                        "child_data_source_ids": ["source-a", "source-b"],
                    }
                },
            )
        if path == "/data_sources/source-a/query":
            return {"results": [{"id": "page-a"}], "has_more": False}
        if path == "/data_sources/source-b/query":
            return {"results": [{"id": "page-b"}], "has_more": False}
        raise AssertionError(f"Unexpected request: {path}")


def test_query_database_falls_back_to_child_data_sources():
    notion = MultipleDataSourceNotion()

    results = notion.query_database("database-id")

    assert results == [{"id": "page-a"}, {"id": "page-b"}]
    assert ("/data_sources/source-a/query", "2025-09-03") in notion.queries
    assert ("/data_sources/source-b/query", "2025-09-03") in notion.queries
