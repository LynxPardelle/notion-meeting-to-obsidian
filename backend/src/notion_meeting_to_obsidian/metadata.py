from __future__ import annotations

from typing import Any


def notion_properties_to_metadata(properties: dict[str, Any]) -> list[dict[str, str]]:
    metadata: list[dict[str, str]] = []
    for name, payload in properties.items():
        property_type = payload.get("type")
        if property_type == "title":
            continue
        value = notion_property_value(payload)
        if not value:
            continue
        metadata.append({"name": name, "type": str(property_type), "value": value})
    return metadata


def notion_property_value(payload: dict[str, Any]) -> str:
    property_type = payload.get("type")
    value = payload.get(property_type)
    if property_type in {"title", "rich_text"}:
        return rich_text_value(value or [])
    if property_type == "people":
        return ", ".join(person.get("name", "") for person in value or [] if person.get("name"))
    if property_type == "date" and value:
        start = value.get("start", "")
        end = value.get("end")
        return f"{start} -> {end}" if end else start
    if property_type in {"select", "status"} and value:
        return value.get("name", "")
    if property_type == "multi_select":
        return ", ".join(item.get("name", "") for item in value or [] if item.get("name"))
    if property_type == "checkbox":
        return "Si" if value else "No"
    if property_type in {"number", "url", "email", "phone_number"}:
        return "" if value is None else str(value)
    if property_type == "relation":
        return ", ".join(item.get("id", "") for item in value or [] if item.get("id"))
    if property_type == "formula" and value:
        return notion_property_value(value)
    if property_type == "rollup" and value:
        rollup_type = value.get("type")
        return notion_property_value({"type": rollup_type, rollup_type: value.get(rollup_type)})
    return ""


def rich_text_value(items: list[dict[str, Any]]) -> str:
    return "".join(item.get("plain_text", "") for item in items)
