#!/usr/bin/env python3
"""Publish or inspect the local public homepage announcement."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collect import load_dotenv  # noqa: E402
from collection_lib.migrations import apply_migrations  # noqa: E402
from collection_lib.public_data import load_homepage_announcement, save_homepage_announcement  # noqa: E402
from collection_lib.repository import CollectionRepository, open_local_connection  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="本机首页公告发布工具")
    subparsers = parser.add_subparsers(dest="command", required=True)
    publish = subparsers.add_parser("publish", help="发布公告到公开快照")
    publish.add_argument("--message", required=True, help="公告正文")
    subparsers.add_parser("show", help="显示当前公告")
    args = parser.parse_args()
    load_dotenv()
    connection = open_local_connection()
    try:
        apply_migrations(connection)
        repository = CollectionRepository(connection)
        if args.command == "publish":
            print(save_homepage_announcement(repository, args.message))
        else:
            print(load_homepage_announcement(repository))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
