"""Single raw-to-staging policy path used by fixtures and approved HTTP adapters."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .contracts import RecordKind, StagingRecord, record_key
from .whitelist import filter_observation


def row_identity(kind: RecordKind, clean: dict[str, Any]) -> dict[str, str]:
    if kind is RecordKind.SHOP_PRODUCT:
        return {"host": str(clean.get("normalized_site") or ""), "canonical_sku": str(clean.get("model_or_plan") or "")}
    if kind is RecordKind.GATEWAY_SITE:
        return {"host": str(clean.get("normalized_site") or "")}
    if kind is RecordKind.OFFICIAL_PLAN:
        return {"plan_slug": str(clean.get("plan_slug") or clean.get("model_or_plan") or ""), "country_code": str(clean.get("country_code") or clean.get("region") or "US")}
    if kind is RecordKind.MODEL_RANK:
        return {"task_slug": str(clean.get("task_slug") or clean.get("platform_family") or "coding"), "model_name": str(clean.get("model_name") or clean.get("model_or_plan") or "")}
    raise ValueError(f"unsupported record kind: {kind}")


def price_is_valid(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number  # NaN check


def process_batch(repository, run_id: str, source_id: str, content_type: str, body: str, rows: list[dict[str, Any]], kind: RecordKind = RecordKind.SHOP_PRODUCT) -> dict[str, int]:
    payload_id = repository.write_raw_payload(run_id, source_id, content_type, hashlib.sha256(body.encode("utf-8")).hexdigest(), body)
    stats = {"raw_records": 0, "skipped_manual": 0, "invalid": 0, "staged": 0}
    for row in rows:
        clean = filter_observation(row)
        clean.setdefault("source_id", source_id)
        try:
            key = record_key(kind, **row_identity(kind, clean))
        except ValueError:
            stats["invalid"] += 1
            continue
        repository.write_raw_record(run_id, source_id, key, kind, clean, payload_id)
        stats["raw_records"] += 1
        if kind is RecordKind.SHOP_PRODUCT and not price_is_valid(clean.get("price")):
            stats["invalid"] += 1
            continue
        if repository.has_manual_override(kind, key):
            stats["skipped_manual"] += 1
            continue
        repository.write_staging_record(StagingRecord(run_id=run_id, record_kind=kind, record_key=key, payload=clean))
        stats["staged"] += 1
    return stats


def run_source_pipeline(repository, source: dict[str, Any], body: str, rows: list[dict[str, Any]], content_type: str, trigger: str, kind: RecordKind, publisher) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("run-%Y%m%d%H%M%S-%f")
    source_id = str(source.get("id") or source.get("source_id") or "")
    repository.create_run(run_id, source_id, trigger)
    try:
        stats = process_batch(repository, run_id, source_id, content_type, body, rows, kind=kind)
        published = publisher.publish_run(repository, run_id)
        repository.finish_run(run_id, "completed")
        repository.commit()
        return {"run_id": run_id, "stats": stats, "published": published, "error": None}
    except Exception as exc:  # noqa: BLE001
        repository.rollback()
        try:
            repository.create_run(run_id, source_id, trigger)
            repository.finish_run(run_id, "failed", str(exc)[:400])
            repository.commit()
        except Exception:
            repository.rollback()
        return {"run_id": run_id, "stats": {}, "published": {"published": 0}, "error": str(exc).split("using password")[0].strip()}
