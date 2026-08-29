"""Explicitly merge one raw batch into runtime tables; this transaction is publication."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .config import source_class_rank
from .contracts import RecordKind
from .publisher import PublicPublisher


_SOURCE_METADATA_FIELDS = {
    "batch_id", "run_id", "source_id", "source_class", "source_priority", "source_url", "source_record_hash",
    "record_kind", "record_key", "validation_state", "validation_reason", "manual_state",
}


def _numeric_price(payload: dict[str, Any]) -> float:
    try:
        value = float(payload.get("price_number") if payload.get("price_number") is not None else payload.get("price"))
    except (TypeError, ValueError):
        return float("inf")
    return value if value == value else float("inf")


def _rank(row: dict[str, Any]) -> tuple[int, int, int]:
    payload = row.get("payload") or {}
    return source_class_rank(
        {
            "id": payload.get("source_id") or row.get("source_id"),
            "source_class": payload.get("source_class") or row.get("source_class"),
            "priority": payload.get("source_priority") if payload.get("source_priority") is not None else row.get("source_priority"),
        }
    )


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def merge_raw_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge valid raw rows by stable key without using display `site.score`."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("validation_state") or (row.get("payload") or {}).get("validation_state") or "valid") != "valid":
            continue
        key = str(row.get("record_key") or (row.get("payload") or {}).get("record_key") or "")
        if key:
            grouped[key].append(row)

    merged: list[dict[str, Any]] = []
    for key, candidates in grouped.items():
        ranked = sorted(candidates, key=lambda row: tuple(-part for part in _rank(row)) + (_numeric_price(row.get("payload") or {}),))
        winner = ranked[0]
        winner_rank = _rank(winner)
        for candidate in ranked[1:]:
            candidate_rank = _rank(candidate)
            if candidate_rank == winner_rank and _numeric_price(candidate.get("payload") or {}) < _numeric_price(winner.get("payload") or {}):
                winner = candidate
                winner_rank = candidate_rank

        payload = dict(winner.get("payload") or {})
        for candidate in ranked:
            if candidate is winner:
                continue
            extra = candidate.get("payload") or {}
            for field, value in extra.items():
                if field not in _SOURCE_METADATA_FIELDS and _missing(payload.get(field)) and not _missing(value):
                    payload[field] = value
        payload["record_key"] = key
        merged.append(
            {
                "record_key": key,
                "record_kind": str(winner.get("record_kind") or payload.get("record_kind") or ""),
                "source_id": str(winner.get("source_id") or payload.get("source_id") or ""),
                "payload": payload,
                "source_rows": len(candidates),
            }
        )
    return sorted(merged, key=lambda row: row["record_key"])


class RuntimeImporter:
    def __init__(self, publisher: PublicPublisher | None = None):
        self.publisher = publisher or PublicPublisher()

    def merge_import_batch(self, repository, batch_id: str) -> dict[str, int | bool | str]:
        """Write a complete runtime snapshot for a completed raw batch, exactly once."""
        batch = repository.get_batch(batch_id)
        if not batch:
            raise ValueError(f"unknown batch: {batch_id}")
        if batch.get("status") == "imported":
            return {"batch_id": batch_id, "runtime_writes": 0, "skipped_manual": 0, "already_imported": True}
        if batch.get("status") != "raw_completed":
            raise ValueError(f"batch is not ready for merge/import: {batch_id}")

        batch_raw_rows = repository.fetch_raw_batch(batch_id)
        batch_keys = {str(row.get("record_key") or (row.get("payload") or {}).get("record_key") or "") for row in batch_raw_rows}
        batch_keys.discard("")
        # A source loop may run one source at a time.  Merge the newest raw row
        # from every known source for the affected stable keys, not just this
        # batch, so a later low-priority source cannot replace a higher-priority
        # current winner.
        raw_rows = repository.fetch_latest_raw_for_keys(batch_keys)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in raw_rows:
            key = str(row.get("record_key") or (row.get("payload") or {}).get("record_key") or "")
            if key:
                grouped[key].append(row)

        eligible: list[dict[str, Any]] = []
        skipped_manual = 0
        for key, rows in grouped.items():
            kind_text = str(rows[0].get("record_kind") or (rows[0].get("payload") or {}).get("record_kind") or "")
            try:
                kind = RecordKind(kind_text)
            except ValueError:
                continue
            if repository.has_manual_override(kind, key):
                skipped_manual += 1
                continue
            eligible.extend(rows)

        merged = merge_raw_records(eligible)
        kinds: set[RecordKind] = set()
        try:
            for row in merged:
                kind = RecordKind(row["record_kind"])
                self.publisher.publish_merged_row(repository, row)
                kinds.add(kind)
            if kinds:
                self.publisher.rebuild_snapshots(repository, kinds)
            repository.mark_batch_imported(batch_id)
            repository.append_activity(
                "collection.merge-import",
                "merge-import",
                f"batch {batch_id} imported {len(merged)} runtime records",
                {"batch_id": batch_id, "runtime_writes": len(merged), "skipped_manual": skipped_manual},
            )
            repository.commit()
        except Exception:
            repository.rollback()
            raise
        return {"batch_id": batch_id, "runtime_writes": len(merged), "skipped_manual": skipped_manual, "already_imported": False}
