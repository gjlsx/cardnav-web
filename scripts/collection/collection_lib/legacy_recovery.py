"""Diagnose and narrowly recover formal rows produced by the legacy direct-publish path."""
from __future__ import annotations

from datetime import datetime, timezone

from .contracts import RecordKind
from .publisher import PublicPublisher
from .runtime_import import merge_raw_records


def _is_recoverable(candidate: dict) -> bool:
    try:
        kind = RecordKind(str(candidate.get("record_kind") or ""))
    except ValueError:
        return False
    key = str(candidate.get("record_key") or "")
    source_id = str(candidate.get("source_id") or "")
    payload = candidate.get("payload") or {}
    if not key or not source_id:
        return False
    if kind is RecordKind.SHOP_PRODUCT:
        return bool(payload.get("normalized_site") and payload.get("model_or_plan"))
    if kind is RecordKind.GATEWAY_SITE:
        return bool(payload.get("normalized_site"))
    if kind is RecordKind.OFFICIAL_PLAN:
        return bool(payload.get("plan_slug") or payload.get("model_or_plan"))
    return bool(payload.get("task_slug") or payload.get("platform_family")) and bool(payload.get("model_name") or payload.get("model_or_plan"))


class LegacyDirectPublishRecovery:
    def __init__(self, publisher: PublicPublisher | None = None):
        self.publisher = publisher or PublicPublisher()

    def diagnose(self, repository) -> dict:
        rows = repository.list_legacy_direct_published()
        imported_winners = {
            row["record_key"]: str(row.get("source_id") or (row.get("payload") or {}).get("source_id") or "")
            for row in merge_raw_records(repository.fetch_imported_raw_records())
        }
        recoverable = [
            row for row in rows
            if _is_recoverable(row) and imported_winners.get(str(row.get("record_key") or "")) != str(row.get("source_id") or "")
        ]
        ambiguous = [row for row in rows if row not in recoverable]
        return {"total": len(rows), "recoverable": len(recoverable), "ambiguous": len(ambiguous), "rows": rows}

    def recover(self, repository, recovery_id: str | None = None) -> dict:
        resolved_id = recovery_id or datetime.now(timezone.utc).strftime("legacy-recovery-%Y%m%d%H%M%S-%f")
        report = self.diagnose(repository)
        kinds: set[RecordKind] = set()
        recovered = 0
        try:
            recoverable_keys = {str(row["record_key"]) for row in report["rows"] if _is_recoverable(row)}
            imported_winners = {
                row["record_key"]: str(row.get("source_id") or (row.get("payload") or {}).get("source_id") or "")
                for row in merge_raw_records(repository.fetch_imported_raw_records())
            }
            for candidate in report["rows"]:
                key = str(candidate.get("record_key") or "")
                if key not in recoverable_keys or imported_winners.get(key) == str(candidate.get("source_id") or ""):
                    continue
                repository.backup_legacy_candidate(resolved_id, candidate)
                if repository.delete_known_legacy_runtime(candidate):
                    repository.mark_legacy_candidate_recovered(candidate)
                    recovered += 1
                    kinds.add(RecordKind(str(candidate["record_kind"])))
            if kinds:
                self.publisher.rebuild_snapshots(repository, kinds)
            repository.commit()
        except Exception:
            repository.rollback()
            raise
        return {"recovery_id": resolved_id, "recovered": recovered, "ambiguous": report["ambiguous"]}
