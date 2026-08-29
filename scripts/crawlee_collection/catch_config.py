"""Shared catch.config for collect/merge CLI, GUI, and Linux one-shot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .sources import PRICEAI_SOURCE_IDS, require_allowed_source, get_source

PACKAGE_DIR = Path(__file__).resolve().parent
CATCH_CONFIG_PATH = PACKAGE_DIR / "catch.config"
CATCH_CONFIG_EXAMPLE_PATH = PACKAGE_DIR / "catch.config.example"

_DEFAULTS = {
    "collect": {
        "enabled": False,
        "source_ids": list(PRICEAI_SOURCE_IDS),
        "max_items_per_run": 1000,
        "interval_seconds": 3600,
    },
    "merge": {
        "enabled": False,
        "poll_interval_seconds": 10,
        "connection_idle_ttl_s": 600,
    },
}


def load_catch_config(path: Path | None = None) -> dict[str, Any]:
    """Load operator knobs. Allowlist URLs stay in code; unknown source ids are rejected."""
    chosen = path or (CATCH_CONFIG_PATH if CATCH_CONFIG_PATH.exists() else CATCH_CONFIG_EXAMPLE_PATH)
    raw = json.loads(chosen.read_text(encoding="utf-8")) if chosen.exists() else {}
    collect = {**_DEFAULTS["collect"], **(raw.get("collect") or {})}
    merge = {**_DEFAULTS["merge"], **(raw.get("merge") or {})}
    source_ids = [str(item) for item in collect.get("source_ids") or []]
    for source_id in source_ids:
        try:
            source = get_source(source_id)
            require_allowed_source(source_id, source.url)
        except ValueError as exc:
            raise ValueError(f"source id is not allowed: {source_id}") from exc
    collect["source_ids"] = source_ids
    collect["enabled"] = bool(collect.get("enabled"))
    collect["max_items_per_run"] = int(collect.get("max_items_per_run") or 0)
    collect["interval_seconds"] = int(collect.get("interval_seconds") or 3600)
    merge["enabled"] = bool(merge.get("enabled"))
    merge["poll_interval_seconds"] = int(merge.get("poll_interval_seconds") or 10)
    merge["connection_idle_ttl_s"] = int(merge.get("connection_idle_ttl_s") or 600)
    return {"collect": collect, "merge": merge}


def configured_sources(path: Path | None = None):
    """Return allowlisted sources enabled in catch.config, in config order."""
    return [get_source(source_id) for source_id in load_catch_config(path)["collect"]["source_ids"]]
