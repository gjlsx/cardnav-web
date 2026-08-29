"""Independent CLI for the Crawlee + Playwright collector."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crawler import PlaywrightPageFetcher
from .database import ReusableRepository
from .parser import parse_priceai_page
from .sources import MAX_CONCURRENCY, get_source, list_sources
from .worker import MergeImportWorker


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Independent Crawlee Playwright collector for allowlisted PriceAI pages")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-config")
    sub.add_parser("list-sources")
    collect = sub.add_parser("collect")
    target = collect.add_mutually_exclusive_group(required=True)
    target.add_argument("--source", dest="source_id")
    target.add_argument("--all", action="store_true")
    sub.add_parser("list-raw")
    merge = sub.add_parser("merge-once")
    merge.add_argument("--batch", default="")
    worker = sub.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    return parser


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))


def _sanitize(error: BaseException) -> str:
    return str(error).split("using password")[0].strip()


def _selected_sources(args: argparse.Namespace):
    if getattr(args, "all", False):
        return list(list_sources())
    return [get_source(args.source_id)]


def cmd_check_config() -> int:
    sources = list_sources()
    _print(
        {
            "max_concurrency": MAX_CONCURRENCY,
            "errors": [],
            "sources": [
                {
                    "source_id": source.source_id,
                    "url": source.url,
                    "page_type": source.page_type,
                    "record_kind": source.record_kind.value,
                    "enabled": source.enabled,
                }
                for source in sources
            ],
        }
    )
    return 0


def cmd_list_sources() -> int:
    return cmd_check_config()


def cmd_collect(args: argparse.Namespace, services: dict[str, Any]) -> int:
    fetcher = services["fetcher"]
    store = services["store"]
    observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    captures = []
    failures = []
    try:
        sources = _selected_sources(args)
    except ValueError as exc:
        _print({"error": _sanitize(exc)})
        return 2
    for source in sources:
        try:
            html = fetcher.fetch_html(source)
            captures.append(parse_priceai_page(source, html, observed_at=observed_at))
        except Exception as exc:  # noqa: BLE001
            failures.append({"source_id": source.source_id, "error": _sanitize(exc)})
    result: dict[str, Any] = {"failures": failures, "batch_id": None, "stats": {"raw_records": 0}}
    if captures:
        persisted = store.persist_captures(captures, trigger="manual")
        result.update(persisted)
    _print(result)
    return 1 if failures or result.get("error") else 0


def cmd_list_raw(services: dict[str, Any]) -> int:
    _print({"batches": services["store"].list_raw_batches()})
    return 0


def cmd_merge_once(args: argparse.Namespace, services: dict[str, Any]) -> int:
    store = services["store"]
    batch_id = args.batch or (store.ready_batch_ids() or [""])[0]
    if not batch_id:
        _print({"error": "merge-once requires a raw_completed batch"})
        return 2
    _print(store.merge_batch(batch_id))
    return 0


def cmd_worker(args: argparse.Namespace, services: dict[str, Any]) -> int:
    worker = MergeImportWorker(services["store"])
    if args.once:
        _print({"results": worker.run_once(), "running": worker.is_running})
        return 0
    worker.start()
    try:
        _print({"running": worker.is_running, "poll_interval_s": worker.poll_interval_s})
        while worker.is_running:
            worker.run_once()
            break
    finally:
        worker.stop()
    return 0


def default_services() -> dict[str, Any]:
    load_dotenv()
    return {"fetcher": PlaywrightPageFetcher(), "store": ReusableRepository()}


def main(argv: list[str] | None = None, services: dict[str, Any] | None = None) -> int:
    args = build_parser().parse_args(argv)
    resolved = services or default_services()
    if args.command == "check-config":
        return cmd_check_config()
    if args.command == "list-sources":
        return cmd_list_sources()
    if args.command == "collect":
        return cmd_collect(args, resolved)
    if args.command == "list-raw":
        return cmd_list_raw(resolved)
    if args.command == "merge-once":
        return cmd_merge_once(args, resolved)
    return cmd_worker(args, resolved)


if __name__ == "__main__":
    raise SystemExit(main())
