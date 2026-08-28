"""Source registry defaults. Sources never carry or override site.score."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_ENABLED = False
DEFAULT_INTERVAL_MINUTES = 60
DEFAULT_MAX_ITEMS_PER_RUN = 1000
UNLIMITED_ITEMS = 0

SOURCE_CLASSES = ("site_api", "site_html", "aggregator")
AGGREGATOR_RANK = {"priceai": 3, "cardnav": 2, "openprice": 1}
CLASS_RANK = {"site_api": 3, "site_html": 2, "aggregator": 1}

DEFAULT_WHITELIST = [
    "normalized_site",
    "source_id",
    "source_class",
    "source_priority",
    "platform_family",
    "model_or_plan",
    "price",
    "currency",
    "billing_unit",
    "stock_status",
    "region",
    "payment_tags",
    "delivery_tags",
    "public_perf",
    "observed_at",
    "provenance",
    "confidence",
]


def default_source(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    source = {
        "id": "",
        "name": "",
        "category": "aggregator",
        "source_class": "aggregator",
        "target_domain": "",
        "priority": 0,
        "enabled": DEFAULT_ENABLED,
        "interval_minutes": DEFAULT_INTERVAL_MINUTES,
        "max_items_per_run": DEFAULT_MAX_ITEMS_PER_RUN,
        "approval_status": "draft",
        "field_whitelist": list(DEFAULT_WHITELIST),
    }
    if overrides:
        source.update(overrides)
    source.pop("score", None)
    source.pop("site_score", None)
    return source


def load_sources(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_sources = payload["sources"] if isinstance(payload, dict) else payload
    return [normalize_source(item) for item in raw_sources]


def save_sources(path: str | Path, sources: list[dict[str, Any]]) -> None:
    Path(path).write_text(
        json.dumps({"sources": [normalize_source(item) for item in sources]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_source(raw: dict[str, Any]) -> dict[str, Any]:
    if "score" in raw or "site_score" in raw:
        raise ValueError("source config must not include score; site.score belongs to the site catalog")
    source = default_source({key: value for key, value in raw.items() if key not in {"score", "site_score"}})
    source["enabled"] = bool(source.get("enabled", DEFAULT_ENABLED))
    source["interval_minutes"] = int(source.get("interval_minutes", DEFAULT_INTERVAL_MINUTES))
    source["max_items_per_run"] = int(source.get("max_items_per_run", DEFAULT_MAX_ITEMS_PER_RUN))
    source["priority"] = int(source.get("priority", 0))
    source["approval_status"] = str(source.get("approval_status") or "draft").strip().lower()
    source["source_class"] = str(source.get("source_class") or source.get("category") or "aggregator").strip().lower()
    if source["source_class"] not in SOURCE_CLASSES:
        source["source_class"] = "aggregator"
    source["field_whitelist"] = list(source.get("field_whitelist") or DEFAULT_WHITELIST)
    if "score" in source or "site_score" in source:
        raise ValueError("source config must not include score; site.score belongs to the site catalog")
    return source


def is_approved(source: dict[str, Any]) -> bool:
    return str(source.get("approval_status") or "").strip().lower() == "approved"


def source_may_request_network(source: dict[str, Any]) -> bool:
    return is_approved(source)


def apply_item_cap(rows: list[Any], max_items_per_run: int) -> list[Any]:
    if max_items_per_run == UNLIMITED_ITEMS:
        return list(rows)
    limit = max(0, int(max_items_per_run))
    return list(rows)[:limit]


def source_class_rank(source: dict[str, Any]) -> tuple[int, int, int]:
    source_class = str(source.get("source_class") or "aggregator")
    class_rank = CLASS_RANK.get(source_class, 0)
    aggregator_rank = 0
    if source_class == "aggregator":
        source_id = str(source.get("id") or source.get("name") or "").lower()
        for key, rank in AGGREGATOR_RANK.items():
            if key in source_id:
                aggregator_rank = rank
                break
    return (class_rank, aggregator_rank, int(source.get("priority") or 0))


def validate_sources(sources: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for source in sources:
        normalized = deepcopy(source)
        try:
            normalized = normalize_source(normalized)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        source_id = normalized["id"]
        if not source_id:
            errors.append("source id is required")
        elif source_id in seen:
            errors.append(f"duplicate source id: {source_id}")
        seen.add(source_id)
        if normalized["interval_minutes"] < 1:
            errors.append(f"{source_id}: interval_minutes must be >= 1")
        if normalized["max_items_per_run"] < 0:
            errors.append(f"{source_id}: max_items_per_run must be >= 0")
        if not normalized["target_domain"]:
            errors.append(f"{source_id}: target_domain is required")
    return errors
