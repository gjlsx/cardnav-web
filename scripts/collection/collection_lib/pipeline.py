"""Single raw-to-staging policy path used by fixtures and approved HTTP adapters."""
from __future__ import annotations

import hashlib
from typing import Any

from .contracts import RecordKind, StagingRecord, record_key
from .whitelist import filter_observation


def process_batch(repository, run_id: str, source_id: str, content_type: str, body: str, rows: list[dict[str, Any]], kind: RecordKind = RecordKind.SHOP_PRODUCT) -> dict[str, int]:
    payload_id = repository.write_raw_payload(run_id, source_id, content_type, hashlib.sha256(body.encode("utf-8")).hexdigest(), body)
    stats = {"raw_records": 0, "skipped_manual": 0, "invalid": 0, "staged": 0}
    for row in rows:
        clean = filter_observation(row)
        try:
            key = record_key(kind, host=str(clean.get("normalized_site") or ""), canonical_sku=str(clean.get("model_or_plan") or ""))
        except ValueError:
            stats["invalid"] += 1
            continue
        repository.write_raw_record(run_id, source_id, key, kind, clean, payload_id)
        stats["raw_records"] += 1
        try:
            valid_price = float(clean.get("price"))
        except (TypeError, ValueError):
            valid_price = None
        if valid_price is None:
            stats["invalid"] += 1
            continue
        if repository.has_manual_override(kind, key):
            stats["skipped_manual"] += 1
            continue
        repository.write_staging_record(StagingRecord(run_id=run_id, record_kind=kind, record_key=key, payload=clean))
        stats["staged"] += 1
    return stats
