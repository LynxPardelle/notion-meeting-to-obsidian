from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


def rich_text_to_markdown(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        text = item.get("plain_text", "")
        href = item.get("href")
        annotations = item.get("annotations", {})
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def rich_text_to_plain_text(items: list[dict[str, Any]]) -> str:
    return "".join(item.get("plain_text", "") for item in items)


def extract_title(page: dict[str, Any]) -> str:
    properties = page.get("properties", {})
    for value in properties.values():
        if value.get("type") == "title":
            title = rich_text_to_plain_text(value.get("title", []))
            if title:
                return title
    return page.get("title") or "Untitled Meeting"


def page_metadata(page: dict[str, Any]) -> dict[str, str]:
    return {
        "title": extract_title(page),
        "notion_id": page.get("id", ""),
        "notion_url": page.get("url", ""),
        "last_edited_time": page.get("last_edited_time", ""),
        "synced_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def yaml_escape(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def frontmatter(metadata: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {yaml_escape(value)}")
    lines.append("---")
    return "\n".join(lines)


def block_to_markdown(block: dict[str, Any]) -> str:
    block_type = block.get("type")
    value = block.get(block_type or "", {})
    text = rich_text_to_markdown(value.get("rich_text", []))

    if block_type == "paragraph":
        return text
    if block_type == "heading_1":
        return f"# {text}"
    if block_type == "heading_2":
        return f"## {text}"
    if block_type == "heading_3":
        return f"### {text}"
    if block_type == "bulleted_list_item":
        return f"- {text}"
    if block_type == "numbered_list_item":
        return f"1. {text}"
    if block_type == "to_do":
        checked = "x" if value.get("checked") else " "
        return f"- [{checked}] {text}"
    if block_type == "quote":
        return "\n".join(f"> {line}" for line in text.splitlines() or [""])
    if block_type == "code":
        language = value.get("language") or ""
        return f"```{language}\n{text}\n```"
    if block_type == "divider":
        return "---"
    if block_type == "callout":
        return f"> [!note]\n> {text}"
    if block_type == "bookmark":
        url = value.get("url", "")
        return f"[{url}]({url})" if url else ""
    if block_type == "child_page":
        title = value.get("title", "Child page")
        return f"[[{title}]]"
    return text


def blocks_to_markdown(blocks: list[dict[str, Any]]) -> str:
    rendered = [block_to_markdown(block).rstrip() for block in blocks]
    return "\n\n".join(line for line in rendered if line)


def page_to_markdown(page: dict[str, Any], blocks: list[dict[str, Any]]) -> str:
    metadata = page_metadata(page)
    body = blocks_to_markdown(blocks)
    title = metadata["title"]
    if not re.search(r"^#\s+", body, re.MULTILINE):
        body = f"# {title}\n\n{body}" if body else f"# {title}"
    return frontmatter(metadata) + "\n\n" + body + "\n"
