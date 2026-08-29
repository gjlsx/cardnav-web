"""Parameterized MySQL persistence for local collection runs."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from .contracts import OverrideState, RecordKind


def open_local_connection():
    """Open one bounded local MySQL session from repository `.env` values."""
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD") or os.environ.get("MYSQL_PWD", ""),
        database=os.environ.get("MYSQL_DATABASE", "ailovemoney"),
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=5,
        read_timeout=15,
        write_timeout=15,
    )


class CollectionRepository:
    def __init__(self, connection):
        self.connection = connection

    def _execute(self, sql: str, params: tuple[Any, ...] = ()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.lastrowid
        finally:
            cursor.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()):
        return self._execute(sql, params)

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        cursor = self.connection.cursor(DictCursor)
        try:
            cursor.execute(sql, params)
            return list(cursor.fetchall() or [])
        finally:
            cursor.close()

    def create_batch(self, batch_id: str, trigger: str) -> None:
        self._execute(
            "INSERT INTO collection_batches (batch_id, trigger_type, status) VALUES (%s, %s, 'running') "
            "ON DUPLICATE KEY UPDATE trigger_type = VALUES(trigger_type), status = 'running', finished_at = NULL, error_summary = NULL",
            (batch_id, trigger),
        )

    def finish_batch(self, batch_id: str, status: str, error_summary: str | None = None) -> None:
        self._execute(
            "UPDATE collection_batches SET status = %s, finished_at = UTC_TIMESTAMP(), error_summary = %s WHERE batch_id = %s",
            (status, error_summary, batch_id),
        )

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        rows = self.query("SELECT batch_id, trigger_type, status, started_at, finished_at, error_summary FROM collection_batches WHERE batch_id = %s", (batch_id,))
        return rows[0] if rows else None

    def fetch_raw_batch(self, batch_id: str) -> list[dict[str, Any]]:
        rows = self.query(
            "SELECT id, batch_id, run_id, source_id, source_class, source_priority, source_url, source_record_hash, record_key, record_kind, payload, captured_at, validation_state, validation_reason "
            "FROM collection_raw_records WHERE batch_id = %s ORDER BY id ASC",
            (batch_id,),
        )
        for row in rows:
            payload = row.get("payload")
            row["payload"] = json.loads(payload) if isinstance(payload, str) else (payload or {})
        return rows

    def fetch_latest_raw_for_keys(self, keys: set[str]) -> list[dict[str, Any]]:
        """Return the newest valid raw row per (stable key, source) for a merge scope."""
        if not keys:
            return []
        placeholders = ", ".join(["%s"] * len(keys))
        rows = self.query(
            "SELECT id, batch_id, run_id, source_id, source_class, source_priority, source_url, source_record_hash, record_key, record_kind, payload, captured_at, validation_state, validation_reason "
            f"FROM collection_raw_records WHERE validation_state = 'valid' AND record_key IN ({placeholders}) ORDER BY id DESC",
            tuple(keys),
        )
        newest: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            key = (str(row.get("record_key") or ""), str(row.get("source_id") or ""))
            if key not in newest:
                payload = row.get("payload")
                row["payload"] = json.loads(payload) if isinstance(payload, str) else (payload or {})
                newest[key] = row
        return list(newest.values())

    def mark_batch_imported(self, batch_id: str) -> None:
        self._execute("UPDATE collection_raw_records SET merged_at = UTC_TIMESTAMP(), imported_at = UTC_TIMESTAMP() WHERE batch_id = %s", (batch_id,))
        self._execute("UPDATE collection_batches SET status = 'imported', finished_at = UTC_TIMESTAMP() WHERE batch_id = %s", (batch_id,))

    def list_legacy_direct_published(self) -> list[dict[str, Any]]:
        rows = self.query(
            "SELECT s.record_kind, s.record_key, s.source_id, s.normalized_site, s.model_or_plan, s.region, s.platform_family, s.observed_at "
            "FROM collection_staging_observations s LEFT JOIN collection_runs r ON r.run_id = s.run_id "
            "WHERE s.publish_status = 'published' AND (r.batch_id IS NULL OR r.batch_id = '')"
        )
        for row in rows:
            row["payload"] = {
                "normalized_site": row.get("normalized_site") or "",
                "model_or_plan": row.get("model_or_plan") or "",
                "region": row.get("region") or "",
                "platform_family": row.get("platform_family") or "",
                "observed_at": row.get("observed_at") or "",
            }
        return rows

    def fetch_imported_raw_records(self) -> list[dict[str, Any]]:
        rows = self.query(
            "SELECT raw.record_key, raw.record_kind, raw.source_id, raw.source_class, raw.source_priority, raw.validation_state, raw.payload "
            "FROM collection_raw_records raw JOIN collection_batches batch ON batch.batch_id = raw.batch_id "
            "WHERE batch.status = 'imported'"
        )
        for row in rows:
            payload = row.get("payload")
            row["payload"] = json.loads(payload) if isinstance(payload, str) else (payload or {})
        return rows

    def backup_legacy_candidate(self, recovery_id: str, candidate: dict[str, Any]) -> None:
        self._execute(
            "INSERT INTO collection_legacy_recovery_backups (recovery_id, record_kind, record_key, source_id, payload) VALUES (%s, %s, %s, %s, %s)",
            (
                recovery_id,
                str(candidate["record_kind"]),
                str(candidate["record_key"]),
                str(candidate["source_id"]),
                json.dumps(candidate.get("payload") or {}, ensure_ascii=False),
            ),
        )

    def delete_known_legacy_runtime(self, candidate: dict[str, Any]) -> bool:
        kind = RecordKind(str(candidate["record_kind"]))
        payload = candidate.get("payload") or {}
        source_id = str(candidate["source_id"])
        if kind is RecordKind.SHOP_PRODUCT:
            host = str(payload.get("normalized_site") or "")
            sku = str(payload.get("model_or_plan") or "")
            if not host or not sku:
                return False
            site_id = f"collected-{host.replace(':', '-').replace('/', '-')[:50]}"
            self._execute("DELETE FROM shop_products WHERE site_id = %s AND standard_product = %s AND source_id = %s AND is_sample = FALSE", (site_id, sku, source_id))
            return True
        if kind is RecordKind.GATEWAY_SITE:
            host = str(payload.get("normalized_site") or "")
            if not host:
                return False
            site_id = f"collected-{host.replace(':', '-').replace('/', '-')[:50]}"
            self._execute("DELETE FROM gateway_model_coverage WHERE site_id = %s AND source_id = %s", (site_id, source_id))
            self._execute("DELETE FROM gateway_sites WHERE site_id = %s AND source_id = %s AND is_sample = FALSE", (site_id, source_id))
            return True
        if kind is RecordKind.OFFICIAL_PLAN:
            plan = str(payload.get("plan_slug") or payload.get("model_or_plan") or "")
            country = str(payload.get("country_code") or payload.get("region") or "US")[:2].upper()
            if not plan:
                return False
            self._execute("DELETE FROM official_prices WHERE url_slug = %s AND country_code = %s AND source_id = %s AND is_sample = FALSE", (plan, country, source_id))
            return True
        task = str(payload.get("task_slug") or payload.get("platform_family") or "")
        model = str(payload.get("model_name") or payload.get("model_or_plan") or "")
        if not task or not model:
            return False
        self._execute("DELETE FROM model_leaderboards WHERE task_slug = %s AND model_name = %s AND source_id = %s AND is_sample = FALSE", (task, model, source_id))
        return True

    def mark_legacy_candidate_recovered(self, candidate: dict[str, Any]) -> None:
        self._execute(
            "UPDATE collection_staging_observations SET publish_status = 'recovered' WHERE record_kind = %s AND record_key = %s AND source_id = %s AND publish_status = 'published'",
            (str(candidate["record_kind"]), str(candidate["record_key"]), str(candidate["source_id"])),
        )

    def create_run(self, run_id: str, source_id: str, trigger: str, batch_id: str | None = None) -> None:
        self._execute(
            "INSERT INTO collection_runs (run_id, source_id, trigger_type, batch_id, status) VALUES (%s, %s, %s, %s, 'running') "
            "ON DUPLICATE KEY UPDATE trigger_type = VALUES(trigger_type), batch_id = VALUES(batch_id), status = 'running', finished_at = NULL, error_summary = NULL",
            (run_id, source_id, trigger, batch_id),
        )

    def finish_run(self, run_id: str, status: str, error_summary: str | None = None) -> None:
        self._execute(
            "UPDATE collection_runs SET status = %s, finished_at = UTC_TIMESTAMP(), error_summary = %s WHERE run_id = %s",
            (status, error_summary, run_id),
        )

    def write_raw_payload(self, run_id: str, source_id: str, content_type: str, body_hash: str, body: str) -> int:
        expiry = datetime.now(timezone.utc) + timedelta(days=30)
        return int(
            self._execute(
                "INSERT INTO collection_raw_payloads (run_id, source_id, content_type, body_hash, body, body_expires_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (run_id, source_id, content_type, body_hash, body, expiry.replace(tzinfo=None)),
            )
            or 0
        )

    def write_raw_record(
        self,
        run_id: str,
        source_id: str,
        stable_key: str,
        kind: RecordKind,
        payload: dict[str, Any],
        raw_payload_id: int | None,
        *,
        batch_id: str | None = None,
        source_class: str | None = None,
        source_priority: int | None = None,
        source_url: str | None = None,
        source_record_hash: str | None = None,
        validation_state: str = "valid",
        validation_reason: str | None = None,
    ) -> int:
        return int(
            self._execute(
                "INSERT INTO collection_raw_records (run_id, source_id, record_key, record_kind, raw_payload_id, payload, batch_id, source_class, source_priority, source_url, source_record_hash, validation_state, validation_reason) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id, source_id, stable_key, kind.value, raw_payload_id, json.dumps(payload, ensure_ascii=False),
                    batch_id, source_class, source_priority, source_url, source_record_hash, validation_state, validation_reason,
                ),
            )
            or 0
        )

    def set_manual_override(self, kind: RecordKind, stable_key: str, state: OverrideState, payload: dict[str, Any] | None = None) -> None:
        self._execute(
            "INSERT INTO collection_manual_overrides (record_kind, record_key, state, payload) VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE state = VALUES(state), payload = VALUES(payload), updated_at = UTC_TIMESTAMP()",
            (kind.value, stable_key, state.value, json.dumps(payload, ensure_ascii=False) if payload is not None else None),
        )

    def clear_manual_override(self, kind: RecordKind, stable_key: str) -> None:
        self._execute("DELETE FROM collection_manual_overrides WHERE record_kind = %s AND record_key = %s", (kind.value, stable_key))

    def has_manual_override(self, kind: RecordKind, stable_key: str) -> bool:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT 1 FROM collection_manual_overrides WHERE record_kind = %s AND record_key = %s LIMIT 1", (kind.value, stable_key))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def upsert_snapshot(self, key: str, payload: Any) -> None:
        self._execute(
            "INSERT INTO public_snapshot_entries (`key`, payload) VALUES (%s, %s) ON DUPLICATE KEY UPDATE payload = VALUES(payload)",
            (key, json.dumps(payload, ensure_ascii=False, default=str)),
        )

    def upsert_source(self, source: dict[str, Any]) -> None:
        self._execute(
            "INSERT INTO collection_sources (source_id, name, source_class, target_domain, priority, enabled, interval_minutes, max_items_per_run, approval_status, field_whitelist, public_url, allowlist_urls, record_kind) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name), source_class = VALUES(source_class), target_domain = VALUES(target_domain), priority = VALUES(priority), enabled = VALUES(enabled), interval_minutes = VALUES(interval_minutes), max_items_per_run = VALUES(max_items_per_run), approval_status = VALUES(approval_status), field_whitelist = VALUES(field_whitelist), public_url = VALUES(public_url), allowlist_urls = VALUES(allowlist_urls), record_kind = VALUES(record_kind)",
            (
                source["id"], source.get("name") or "", source.get("source_class") or "aggregator",
                source.get("target_domain") or "", int(source.get("priority") or 0), bool(source.get("enabled")),
                int(source.get("interval_minutes") or 60), int(source.get("max_items_per_run") or 1000),
                source.get("approval_status") or "draft", json.dumps(source.get("field_whitelist") or [], ensure_ascii=False),
                source.get("public_url") or "", json.dumps(source.get("allowlist_urls") or [], ensure_ascii=False),
                source.get("record_kind") or "shop_product",
            ),
        )

    def list_sources(self) -> list[dict[str, Any]]:
        return self.query("SELECT source_id AS id, name, source_class, target_domain, priority, enabled, interval_minutes, max_items_per_run, approval_status, public_url, allowlist_urls, record_kind FROM collection_sources ORDER BY source_id")

    def list_staging(self, kind: str, limit: int = 200) -> list[dict[str, Any]]:
        return self.query(
            "SELECT id, record_key, record_kind, normalized_site, model_or_plan, price, currency, quality_status, publish_status, observed_at FROM collection_staging_observations WHERE record_kind = %s ORDER BY id DESC LIMIT %s",
            (kind, limit),
        )

    def list_batches(self, kind: str, limit: int = 80) -> list[dict[str, Any]]:
        """Return capture batches that contain the requested child-tab entity kind."""
        return self.query(
            "SELECT batch.batch_id, batch.trigger_type, batch.status, batch.started_at, batch.finished_at, "
            "COUNT(raw.id) AS raw_count, COUNT(DISTINCT raw.source_id) AS source_count "
            "FROM collection_batches batch JOIN collection_raw_records raw ON raw.batch_id = batch.batch_id "
            "WHERE raw.record_kind = %s GROUP BY batch.batch_id, batch.trigger_type, batch.status, batch.started_at, batch.finished_at "
            "ORDER BY batch.started_at DESC LIMIT %s",
            (kind, limit),
        )

    def list_raw_records(self, kind: str, batch_id: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        sql = (
            "SELECT id, batch_id, run_id, source_id, record_key, record_kind, validation_state, validation_reason, payload "
            "FROM collection_raw_records WHERE record_kind = %s"
        )
        params: list[Any] = [kind]
        if batch_id:
            sql += " AND batch_id = %s"
            params.append(batch_id)
        sql += " ORDER BY id DESC LIMIT %s"
        params.append(limit)
        rows = self.query(sql, tuple(params))
        for row in rows:
            payload = row.get("payload")
            row["payload"] = json.loads(payload) if isinstance(payload, str) else (payload or {})
        return rows

    def list_runtime_records(self, kind: RecordKind, limit: int = 300) -> list[dict[str, Any]]:
        """Expose only current runtime values; raw/staging remain separate audit surfaces."""
        if kind is RecordKind.SHOP_PRODUCT:
            return self.query(
                "SELECT CONCAT(site_id, ':', standard_product) AS runtime_key, site_id, source_id, standard_product AS label, price_number AS value, sampled_at "
                "FROM shop_products WHERE is_sample = FALSE ORDER BY refreshed_at DESC LIMIT %s", (limit,)
            )
        if kind is RecordKind.GATEWAY_SITE:
            return self.query(
                "SELECT site_id AS runtime_key, site_id, source_id, name AS label, score AS value, sampled_at "
                "FROM gateway_sites WHERE is_sample = FALSE ORDER BY sampled_at DESC LIMIT %s", (limit,)
            )
        if kind is RecordKind.OFFICIAL_PLAN:
            return self.query(
                "SELECT CONCAT(url_slug, ':', country_code) AS runtime_key, source_id, display_name AS label, price_value AS value, sampled_at "
                "FROM official_prices WHERE is_sample = FALSE ORDER BY sampled_at DESC LIMIT %s", (limit,)
            )
        return self.query(
            "SELECT CONCAT(task_slug, ':', model_name) AS runtime_key, source_id, model_name AS label, score AS value, sampled_at "
            "FROM model_leaderboards WHERE is_sample = FALSE ORDER BY sampled_at DESC LIMIT %s", (limit,)
        )

    def list_overrides(self, kind: str) -> list[dict[str, Any]]:
        return self.query("SELECT record_kind, record_key, state, updated_at FROM collection_manual_overrides WHERE record_kind = %s ORDER BY updated_at DESC", (kind,))

    def hidden_keys(self, kind: str) -> set[str]:
        return {str(row["record_key"]) for row in self.query("SELECT record_key FROM collection_manual_overrides WHERE record_kind = %s AND state = 'hidden'", (kind,))}

    def append_activity(self, page_key: str, action: str, message: str, details: dict[str, Any] | None = None) -> None:
        self._execute(
            "INSERT INTO console_activity_logs (page_key, action, message, details) VALUES (%s, %s, %s, %s)",
            (page_key, action, message, json.dumps(details, ensure_ascii=False) if details else None),
        )

    def recent_activity(self, page_key: str, limit: int = 80) -> list[dict[str, Any]]:
        return self.query(
            "SELECT page_key, action, message, created_at FROM console_activity_logs WHERE page_key = %s ORDER BY id DESC LIMIT %s",
            (page_key, limit),
        )

    def purge_expired_payload_bodies(self) -> None:
        self._execute("UPDATE collection_raw_payloads SET body = NULL WHERE body_expires_at < UTC_TIMESTAMP() AND body IS NOT NULL")

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()
