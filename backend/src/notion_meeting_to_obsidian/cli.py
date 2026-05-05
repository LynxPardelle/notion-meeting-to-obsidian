from __future__ import annotations

import argparse
import os
import sys

from .config import Config, ConfigError
from .sync import MeetingSyncService


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        raise SystemExit(f"{name} must be an integer, got {value!r}")


def sync_command(args: argparse.Namespace) -> int:
    try:
        config = Config.from_env()
        result = MeetingSyncService(config).sync(force=args.force)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    for note in result.synced:
        print(f"synced: {note.title} -> {note.file_path}")
    for note in result.skipped:
        print(f"skipped: {note.title}")
    print(f"done: {len(result.synced)} synced, {len(result.skipped)} skipped")
    return 0


def serve_command(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "notion_meeting_to_obsidian.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notion-meeting-to-obsidian")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync Notion meeting notes to Obsidian.")
    sync_parser.add_argument("--force", action="store_true", help="Regenerate all notes.")
    sync_parser.set_defaults(func=sync_command)

    serve_parser = subparsers.add_parser("serve", help="Run the local FastAPI server.")
    serve_parser.add_argument("--host", default=os.getenv("BIND_HOST", "127.0.0.1"))
    serve_parser.add_argument("--port", type=int, default=env_int("BACKEND_PORT", 8765))
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.set_defaults(func=serve_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
