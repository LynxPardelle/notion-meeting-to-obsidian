from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class NotionApiError(RuntimeError):
    """Raised when the Notion API returns an error."""


class NotionClient:
    base_url = "https://api.notion.com/v1"

    def __init__(self, token: str, notion_version: str = "2022-06-28") -> None:
        self.token = token
        self.notion_version = notion_version

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Notion-Version": self.notion_version,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            raise NotionApiError(f"Notion API error {exc.code}: {detail}") from exc

    def query_database(self, database_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        payload: dict[str, Any] = {"page_size": 50}
        while True:
            data = self._request("POST", f"/databases/{database_id}/query", payload)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            payload["start_cursor"] = data.get("next_cursor")

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        return self._request("GET", f"/pages/{page_id}")

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
