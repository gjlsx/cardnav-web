"""Shared catch.config for collect/merge CLI, GUI, and Linux one-shot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .sources import GATEWAY_REFERENCE_SOURCE_IDS, PRICEAI_SOURCE_IDS, require_allowed_source, get_source

PACKAGE_DIR = Path(__file__).resolve().parent
CATCH_CONFIG_PATH = PACKAGE_DIR / "catch.config"
CATCH_CONFIG_EXAMPLE_PATH = PACKAGE_DIR / "catch.config.example"

_DEFAULTS = {
    "collect": {
        "enabled": False,
        "source_ids": [*PRICEAI_SOURCE_IDS, *GATEWAY_REFERENCE_SOURCE_IDS],
        "max_items_per_run": 1000,
        "interval_seconds": 3600,
        "source_settings": {
            "hvoyai-awesome-ai-api": {"enabled": False, "interval_minutes": 480},
        },
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
    raw_settings = collect.get("source_settings") or {}
    if not isinstance(raw_settings, dict):
        raise ValueError("collect.source_settings must be an object")
    source_settings: dict[str, dict[str, Any]] = {}
    for source_id, defaults in _DEFAULTS["collect"]["source_settings"].items():
        configured = raw_settings.get(source_id) or {}
        if not isinstance(configured, dict):
            raise ValueError(f"source setting must be an object: {source_id}")
        interval_minutes = int(configured.get("interval_minutes", defaults["interval_minutes"]) or 0)
        if interval_minutes < 1:
            raise ValueError(f"source setting interval_minutes must be positive: {source_id}")
        source_settings[source_id] = {
            "enabled": bool(configured.get("enabled", defaults["enabled"])),
            "interval_minutes": interval_minutes,
        }
    for source_id in raw_settings:
        if source_id not in source_settings:
            raise ValueError(f"source setting is not allowed: {source_id}")
    collect["source_settings"] = source_settings
    merge["enabled"] = bool(merge.get("enabled"))
    merge["poll_interval_seconds"] = int(merge.get("poll_interval_seconds") or 10)
    merge["connection_idle_ttl_s"] = int(merge.get("connection_idle_ttl_s") or 600)
    return {"collect": collect, "merge": merge}


def source_interval_seconds(config: dict[str, Any], source_id: str) -> int:
    """Return the configured local loop cadence for one exact source id."""
    settings = config.get("collect", {}).get("source_settings", {}).get(source_id)
    if isinstance(settings, dict):
        return int(settings["interval_minutes"]) * 60
    return int(config["collect"]["interval_seconds"])


def configured_sources(path: Path | None = None):
    """Return allowlisted sources enabled in catch.config, in config order."""
    return [get_source(source_id) for source_id in load_catch_config(path)["collect"]["source_ids"]]
