from __future__ import annotations

from dataclasses import dataclass, field
import re


HEADING_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")
TASK_RE = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")


@dataclass(frozen=True)
class MeetingTask:
    text: str
    checked: bool = False


@dataclass(frozen=True)
class MeetingCard:
    summary: str = ""
    tasks: list[MeetingTask] = field(default_factory=list)
    notes: str = ""


def parse_meeting_card(markdown: str) -> MeetingCard:
    sections = _section_map(markdown)
    notes = sections.get("Notas", "").strip()
    return MeetingCard(
        summary=sections.get("Resumen", "").strip(),
        tasks=_parse_tasks(sections.get("Tareas", "")),
        notes=notes or _unsectioned_body(markdown),
    )


def update_meeting_card_sections(markdown: str, card: MeetingCard) -> str:
    result = markdown.rstrip()
    replacements = {
        "Resumen": card.summary.strip(),
        "Tareas": _format_tasks(card.tasks),
        "Notas": card.notes.strip(),
    }

    for heading, content in replacements.items():
        result = _replace_or_append_section(result, heading, content)

    return result.rstrip() + "\n"


def _section_map(markdown: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[heading] = markdown[start:end].strip()
    return sections


def _unsectioned_body(markdown: str) -> str:
    body = _strip_frontmatter(markdown)
    first_section = HEADING_RE.search(body)
    if first_section:
        body = body[: first_section.start()]
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines = lines[1:]
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _strip_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown
    end = markdown.find("\n---", 3)
    if end == -1:
        return markdown
    after = markdown.find("\n", end + 4)
    return markdown[after + 1 :] if after != -1 else ""


def _parse_tasks(raw: str) -> list[MeetingTask]:
    tasks: list[MeetingTask] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = TASK_RE.match(stripped)
        if match:
            tasks.append(MeetingTask(text=match.group(2).strip(), checked=match.group(1).lower() == "x"))
        elif stripped.startswith("- "):
            tasks.append(MeetingTask(text=stripped[2:].strip(), checked=False))
        else:
            tasks.append(MeetingTask(text=stripped, checked=False))
    return tasks


def _format_tasks(tasks: list[MeetingTask]) -> str:
    return "\n".join(f"- [{'x' if task.checked else ' '}] {task.text.strip()}" for task in tasks if task.text.strip())


def _replace_or_append_section(markdown: str, heading: str, content: str) -> str:
    matches = list(HEADING_RE.finditer(markdown))
    for index, match in enumerate(matches):
        if match.group(1).strip() != heading:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        return markdown[:start].rstrip() + "\n\n" + content.rstrip() + "\n\n" + markdown[end:].lstrip()

    return markdown.rstrip() + f"\n\n## {heading}\n\n{content.rstrip()}\n"
