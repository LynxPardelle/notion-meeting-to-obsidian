from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class NotionApiError(RuntimeError):
    """Raised when the Notion API returns an error."""

    def __init__(self, message: str, status: int | None = None, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail


class NotionClient:
    base_url = "https://api.notion.com/v1"

    def __init__(self, token: str, notion_version: str = "2022-06-28") -> None:
        self.token = token
        self.notion_version = notion_version

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        notion_version: str | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Notion-Version": notion_version or self.notion_version,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            parsed_detail: dict[str, Any] | None = None
            try:
                parsed = json.loads(detail)
                if isinstance(parsed, dict):
                    parsed_detail = parsed
            except json.JSONDecodeError:
                parsed_detail = None
            raise NotionApiError(f"Notion API error {exc.code}: {detail}", status=exc.code, detail=parsed_detail) from exc

    def query_database(self, database_id: str) -> list[dict[str, Any]]:
        try:
            return self._query_paginated("POST", f"/databases/{database_id}/query")
        except NotionApiError as exc:
            data_source_ids = self._multiple_data_source_ids(exc)
            if not data_source_ids:
                raise
            results: list[dict[str, Any]] = []
            for data_source_id in data_source_ids:
                results.extend(self.query_data_source(data_source_id))
            return results

    def query_data_source(self, data_source_id: str) -> list[dict[str, Any]]:
        return self._query_paginated(
            "POST",
            f"/data_sources/{data_source_id}/query",
            notion_version="2025-09-03",
        )

    def _query_paginated(
        self,
        method: str,
        path: str,
        notion_version: str | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        payload: dict[str, Any] = {"page_size": 50}
        while True:
            data = self._request(method, path, payload, notion_version=notion_version)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            payload["start_cursor"] = data.get("next_cursor")

    def _multiple_data_source_ids(self, exc: NotionApiError) -> list[str]:
        if exc.status != 400 or not exc.detail:
            return []
        additional_data = exc.detail.get("additional_data")
        if not isinstance(additional_data, dict):
            return []
        if additional_data.get("error_type") != "multiple_data_sources_for_database":
            return []
        data_source_ids = additional_data.get("child_data_source_ids")
        if not isinstance(data_source_ids, list):
            return []
        return [data_source_id for data_source_id in data_source_ids if isinstance(data_source_id, str)]

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        return self._request("GET", f"/pages/{page_id}")

    def search_pages(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        payload: dict[str, Any] = {
            "page_size": 50,
            "filter": {"value": "page", "property": "object"},
        }
        while True:
            data = self._request("POST", "/search", payload)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            payload["start_cursor"] = data.get("next_cursor")

    def retrieve_block_children(self, block_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        start_cursor: str | None = None
        while True:
            suffix = f"&start_cursor={start_cursor}" if start_cursor else ""
            data = self._request("GET", f"/blocks/{block_id}/children?page_size=100{suffix}")
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            start_cursor = data.get("next_cursor")

    def retrieve_block_children_recursive(self, block_id: str) -> list[dict[str, Any]]:
        blocks = self.retrieve_block_children(block_id)
        for block in blocks:
            if block.get("has_children") and block.get("type") != "child_page":
                block["_children"] = self.retrieve_block_children_recursive(block["id"])
        return blocks
