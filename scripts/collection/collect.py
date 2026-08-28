#!/usr/bin/env python3
"""Local collection CLI. Fixture/dry-run only unless a source is approved; never publishes."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collection_lib.config import (  # noqa: E402
    apply_item_cap,
    load_sources,
    source_may_request_network,
    validate_sources,
)
from collection_lib.fixtures import fixtures_for_source  # noqa: E402
from collection_lib.fetch import fetch_approved_json  # noqa: E402
from collection_lib.merge import merge_observations  # noqa: E402
from collection_lib.migrations import apply_migrations  # noqa: E402
from collection_lib.repository import open_local_connection  # noqa: E402
from collection_lib.staging import dump_jsonl, write_staging  # noqa: E402
from collection_lib.whitelist import filter_observation  # noqa: E402

DEFAULT_SOURCES = ROOT / "sources.example.json"


def load_dotenv() -> None:
    env_path = ROOT.parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def collect_rows(sources, ignore_enabled: bool) -> tuple[list[dict], dict]:
    stats = {"considered": 0, "skipped_unapproved": 0, "skipped_disabled": 0, "capped": 0, "network_requests": 0}
    collected: list[dict] = []
    sources_by_id = {source["id"]: source for source in sources}
    for source in sources:
        stats["considered"] += 1
        if not ignore_enabled and not source.get("enabled"):
            stats["skipped_disabled"] += 1
            continue
        if not source_may_request_network(source):
            stats["skipped_unapproved"] += 1
            rows = fixtures_for_source(source["id"])
        else:
            _body, rows, _content_type = fetch_approved_json(source)
            stats["network_requests"] += 1
        before = len(rows)
        rows = apply_item_cap(rows, int(source.get("max_items_per_run") or 0))
        stats["capped"] += max(0, before - len(rows))
        for row in rows:
            observation = filter_observation(row)
            observation["source_id"] = source["id"]
            observation["source_class"] = source["source_class"]
            observation["source_priority"] = source["priority"]
            collected.append(observation)
    merged = merge_observations(collected, sources_by_id)
    return merged, {**stats, "raw": len(collected), "merged": len(merged)}


def cmd_check_config(path: Path) -> int:
    sources = load_sources(path)
    errors = validate_sources(sources)
    print(json.dumps({"sources": len(sources), "errors": errors, "defaults": {"enabled": False, "interval_minutes": 60, "max_items_per_run": 1000}}, ensure_ascii=False))
    return 1 if errors else 0


def cmd_dry_run(path: Path, ignore_enabled: bool) -> int:
    sources = load_sources(path)
    rows, stats = collect_rows(sources, ignore_enabled=ignore_enabled)
    print(json.dumps({"stats": stats, "rows": rows}, ensure_ascii=False, indent=2))
    return 0


def cmd_write_staging(path: Path, ignore_enabled: bool) -> int:
    load_dotenv()
    sources = load_sources(path)
    rows, stats = collect_rows(sources, ignore_enabled=ignore_enabled)
    run_id = datetime.now(timezone.utc).strftime("fixture-%Y%m%d%H%M%S")
    dump_jsonl(ROOT / "out" / f"{run_id}.jsonl", rows)
    mysql_counts = {}
    try:
        mysql_counts = write_staging(run_id, rows)
    except Exception as exc:  # noqa: BLE001
        mysql_counts = {"mysql_error": str(exc).split("using password")[0].strip()}
    print(json.dumps({"run_id": run_id, "stats": stats, "mysql": mysql_counts, "published": False}, ensure_ascii=False))
    return 0


def cmd_migrate() -> int:
    load_dotenv()
    connection = open_local_connection()
    try:
        apply_migrations(connection)
    finally:
        connection.close()
    print(json.dumps({"migrated": True, "staging_table": "collection_staging_observations"}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Local collection CLI (fixture/dry-run, no scheduler, no auto-publish)")
    parser.add_argument("command", choices=["check-config", "dry-run", "write-staging", "migrate"])
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--manual", action="store_true", help="Ignore enabled=false (default for dry-run/write-staging)")
    parser.add_argument("--scheduled", action="store_true", help="Honor enabled=false (not used; scheduler is not installed)")
    args = parser.parse_args()
    path = Path(args.sources)
    ignore_enabled = not args.scheduled
    if args.command == "check-config":
        return cmd_check_config(path)
    if args.command == "migrate":
        return cmd_migrate()
    if args.command == "dry-run":
        return cmd_dry_run(path, ignore_enabled=ignore_enabled)
    return cmd_write_staging(path, ignore_enabled=True)


if __name__ == "__main__":
    raise SystemExit(main())
