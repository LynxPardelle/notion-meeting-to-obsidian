from __future__ import annotations

import re
from pathlib import Path


WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def safe_filename(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .")
    name = re.sub(r"\s+", " ", name)
    if not name:
        name = "Untitled Meeting"
    if name.upper() in WINDOWS_RESERVED_NAMES:
        name = f"{name}-note"
    return name[:120] + ".md"


def write_markdown(meetings_dir: Path, title: str, markdown: str) -> Path:
    meetings_dir.mkdir(parents=True, exist_ok=True)
    path = meetings_dir / safe_filename(title)
    path.write_text(markdown, encoding="utf-8", newline="\n")
    return path
