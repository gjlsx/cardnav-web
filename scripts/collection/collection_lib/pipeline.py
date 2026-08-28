"""Raw-first collection batches. Runtime merge/import is a separate service."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .contracts import RecordKind, record_key
from .whitelist import filter_observation


RAW_FIELDS = (
    "batch_id", "run_id", "source_id", "source_class", "source_priority", "source_url", "source_record_hash",
    "record_kind", "record_key", "canonical_site", "canonical_sku", "plan_slug", "country_code", "task_slug",
    "normalised_model", "normalized_site", "platform_family", "product_type", "display_name", "site_name",
    "model_or_plan", "model_name", "model_family", "currency", "price_text", "price_number", "price",
    "billing_unit", "stock_status", "region", "payment_tags", "delivery_tags", "public_perf", "observed_at",
    "provenance", "confidence", "channel_count", "available_channel_count", "out_of_stock_channel_count",
    "validation_state", "validation_reason", "manual_state", "metadata_json",
)


@dataclass(frozen=True)
class SourceCapture:
    source: Mapping[str, Any]
    body: str
    rows: list[dict[str, Any]]
    content_type: str
    kind: RecordKind


def row_identity(kind: RecordKind, clean: Mapping[str, Any]) -> dict[str, str]:
    if kind is RecordKind.SHOP_PRODUCT:
        return {"host": str(clean.get("normalized_site") or ""), "canonical_sku": str(clean.get("canonical_sku") or clean.get("model_or_plan") or "")}
    if kind is RecordKind.GATEWAY_SITE:
        return {"host": str(clean.get("normalized_site") or "")}
    if kind is RecordKind.OFFICIAL_PLAN:
        return {"plan_slug": str(clean.get("plan_slug") or clean.get("model_or_plan") or ""), "country_code": str(clean.get("country_code") or clean.get("region") or "US")}
    if kind is RecordKind.MODEL_RANK:
        return {"task_slug": str(clean.get("task_slug") or clean.get("platform_family") or "coding"), "model_name": str(clean.get("model_name") or clean.get("model_or_plan") or "")}
    raise ValueError(f"unsupported record kind: {kind}")


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _row_hash(row: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(row), ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_raw_observation(
    row: Mapping[str, Any],
    source: Mapping[str, Any],
    kind: RecordKind,
    *,
    batch_id: str | None,
    run_id: str,
) -> tuple[str, dict[str, Any], str, str | None]:
    """Convert allowed source fields into the fixed, nullable project raw schema."""
    clean = filter_observation(dict(row))
    payload = {field: None for field in RAW_FIELDS}
    payload.update(clean)
    source_id = str(source.get("id") or source.get("source_id") or "")
    payload.update(
        {
            "batch_id": batch_id,
            "run_id": run_id,
            "source_id": source_id,
            "source_class": str(source.get("source_class") or "aggregator"),
            "source_priority": int(source.get("priority") or 0),
            "source_url": str(source.get("public_url") or "") or None,
            "source_record_hash": _row_hash(row),
            "record_kind": kind.value,
            "canonical_site": clean.get("normalized_site") or None,
            "canonical_sku": clean.get("canonical_sku") or (clean.get("model_or_plan") if kind is RecordKind.SHOP_PRODUCT else None),
            "normalised_model": clean.get("model_name") or (clean.get("model_or_plan") if kind is RecordKind.MODEL_RANK else None),
            "product_type": clean.get("product_type") or None,
            "display_name": clean.get("display_name") or clean.get("site_name") or None,
            "price_text": str(clean["price"]) if clean.get("price") is not None else None,
            "price_number": _number(clean.get("price")),
            "channel_count": clean.get("channel_count"),
            "available_channel_count": clean.get("available_channel_count"),
            "out_of_stock_channel_count": clean.get("out_of_stock_channel_count"),
            "metadata_json": {},
            "validation_state": "valid",
            "validation_reason": None,
            "manual_state": None,
        }
    )
    try:
        stable_key = record_key(kind, **row_identity(kind, payload))
    except ValueError as exc:
        stable_key = f"invalid:{source_id or 'source'}:{payload['source_record_hash'][:16]}"
        payload["validation_state"] = "invalid"
        payload["validation_reason"] = str(exc)
        payload["record_key"] = stable_key
        return stable_key, payload, "invalid", str(exc)
    payload["record_key"] = stable_key
    return stable_key, payload, "valid", None


def process_batch(
    repository,
    run_id: str,
    source_id: str,
    content_type: str,
    body: str,
    rows: list[dict[str, Any]],
    kind: RecordKind = RecordKind.SHOP_PRODUCT,
    should_stop: Callable[[], bool] = lambda: False,
    *,
    source: Mapping[str, Any] | None = None,
    batch_id: str | None = None,
) -> dict[str, int | bool]:
    """Persist one source response as raw records only; never write staging/runtime data."""
    source = dict(source or {"id": source_id})
    source.setdefault("id", source_id)
    payload_id = repository.write_raw_payload(run_id, source_id, content_type, hashlib.sha256(body.encode("utf-8")).hexdigest(), body)
    stats: dict[str, int | bool] = {"raw_records": 0, "manual_marked": 0, "invalid": 0, "staged": 0, "stopped": False}
    for row in rows:
        if should_stop():
            stats["stopped"] = True
            break
        stable_key, payload, validation_state, validation_reason = normalize_raw_observation(row, source, kind, batch_id=batch_id, run_id=run_id)
        if repository.has_manual_override(kind, stable_key):
            payload["manual_state"] = "locked"
            stats["manual_marked"] = int(stats["manual_marked"]) + 1
        repository.write_raw_record(
            run_id,
            source_id,
            stable_key,
            kind,
            payload,
            payload_id,
            batch_id=batch_id,
            source_class=str(payload["source_class"] or ""),
            source_priority=int(payload["source_priority"] or 0),
            source_url=payload["source_url"],
            source_record_hash=str(payload["source_record_hash"]),
            validation_state=validation_state,
            validation_reason=validation_reason,
        )
        stats["raw_records"] = int(stats["raw_records"]) + 1
        if validation_state != "valid":
            stats["invalid"] = int(stats["invalid"]) + 1
    return stats


def _new_id(prefix: str) -> str:
    return datetime.now(timezone.utc).strftime(f"{prefix}-%Y%m%d%H%M%S-%f")


def run_collection_batch(
    repository,
    captures: Sequence[SourceCapture],
    *,
    trigger: str,
    batch_id: str | None = None,
    should_stop: Callable[[], bool] = lambda: False,
) -> dict[str, Any]:
    """Run one or more source captures under a shared raw-only batch identifier."""
    resolved_batch_id = batch_id or _new_id("batch")
    repository.create_batch(resolved_batch_id, trigger)
    all_stats: dict[str, int | bool] = {"raw_records": 0, "manual_marked": 0, "invalid": 0, "staged": 0, "stopped": False}
    runs: list[str] = []
    try:
        for capture in captures:
            if should_stop():
                all_stats["stopped"] = True
                break
            source_id = str(capture.source.get("id") or capture.source.get("source_id") or "")
            run_id = _new_id("run")
            runs.append(run_id)
            repository.create_run(run_id, source_id, trigger, resolved_batch_id)
            stats = process_batch(
                repository,
                run_id,
                source_id,
                capture.content_type,
                capture.body,
                capture.rows,
                kind=capture.kind,
                should_stop=should_stop,
                source=capture.source,
                batch_id=resolved_batch_id,
            )
            repository.finish_run(run_id, "stopped" if stats["stopped"] else "completed")
            for key in ("raw_records", "manual_marked", "invalid", "staged"):
                all_stats[key] = int(all_stats[key]) + int(stats[key])
            if stats["stopped"]:
                all_stats["stopped"] = True
                break
        repository.finish_batch(resolved_batch_id, "stopped" if all_stats["stopped"] else "raw_completed")
        repository.commit()
        return {
            "batch_id": resolved_batch_id,
            "run_id": runs[0] if len(runs) == 1 else None,
            "run_ids": runs,
            "stats": all_stats,
            "runtime_writes": 0,
            "published": {"published": 0},
            "stopped": bool(all_stats["stopped"]),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        repository.rollback()
        try:
            repository.create_batch(resolved_batch_id, trigger)
            repository.finish_batch(resolved_batch_id, "failed", str(exc)[:400])
            repository.commit()
        except Exception:
            repository.rollback()
        return {
            "batch_id": resolved_batch_id,
            "run_id": runs[0] if len(runs) == 1 else None,
            "run_ids": runs,
            "stats": all_stats,
            "runtime_writes": 0,
            "published": {"published": 0},
            "stopped": False,
            "error": str(exc).split("using password")[0].strip(),
        }


def run_source_pipeline(
    repository,
    source: dict[str, Any],
    body: str,
    rows: list[dict[str, Any]],
    content_type: str,
    trigger: str,
    kind: RecordKind,
    publisher=None,
    should_stop: Callable[[], bool] = lambda: False,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Compatibility entry point: one source becomes one raw-only batch; publisher is ignored."""
    del publisher
    return run_collection_batch(
        repository,
        [SourceCapture(source=source, body=body, rows=rows, content_type=content_type, kind=kind)],
        trigger=trigger,
        batch_id=batch_id,
        should_stop=should_stop,
    )
