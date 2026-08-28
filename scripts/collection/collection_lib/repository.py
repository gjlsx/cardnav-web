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

    def create_run(self, run_id: str, source_id: str, trigger: str) -> None:
        self._execute(
            "INSERT INTO collection_runs (run_id, source_id, trigger_type, status) VALUES (%s, %s, %s, 'running') "
            "ON DUPLICATE KEY UPDATE trigger_type = VALUES(trigger_type), status = 'running', finished_at = NULL, error_summary = NULL",
            (run_id, source_id, trigger),
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

    def write_raw_record(self, run_id: str, source_id: str, stable_key: str, kind: RecordKind, payload: dict[str, Any], raw_payload_id: int | None) -> int:
        return int(
            self._execute(
                "INSERT INTO collection_raw_records (run_id, source_id, record_key, record_kind, raw_payload_id, payload) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (run_id, source_id, stable_key, kind.value, raw_payload_id, json.dumps(payload, ensure_ascii=False)),
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

    def write_staging_record(self, record) -> None:
        payload = dict(record.payload)
        self._execute(
            "INSERT INTO collection_staging_observations (run_id, normalized_site, source_id, source_class, source_priority, platform_family, model_or_plan, price, currency, billing_unit, stock_status, region, payment_tags, delivery_tags, public_perf, observed_at, provenance, confidence, record_key, record_kind, quality_status, publish_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved', 'pending')",
            (record.run_id, payload.get("normalized_site", ""), payload.get("source_id", ""), payload.get("source_class", ""), payload.get("source_priority", 0), payload.get("platform_family", ""), payload.get("model_or_plan", ""), payload.get("price"), payload.get("currency", ""), payload.get("billing_unit", ""), payload.get("stock_status", ""), payload.get("region", ""), payload.get("payment_tags", ""), payload.get("delivery_tags", ""), payload.get("public_perf", ""), payload.get("observed_at", ""), payload.get("provenance", ""), payload.get("confidence"), record.record_key, record.record_kind.value),
        )

    def fetch_pending_staging(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.query(
            "SELECT id, run_id, normalized_site, source_id, source_class, source_priority, platform_family, model_or_plan, price, currency, billing_unit, stock_status, region, payment_tags, delivery_tags, public_perf, observed_at, provenance, confidence, record_key, record_kind FROM collection_staging_observations WHERE run_id = %s AND publish_status = 'pending' AND quality_status = 'approved'",
            (run_id,),
        )
        for row in rows:
            row["payload"] = {
                "normalized_site": row.get("normalized_site") or "",
                "source_id": row.get("source_id") or "",
                "source_class": row.get("source_class") or "",
                "source_priority": row.get("source_priority") or 0,
                "platform_family": row.get("platform_family") or "",
                "model_or_plan": row.get("model_or_plan") or "",
                "price": row.get("price"),
                "currency": row.get("currency") or "",
                "billing_unit": row.get("billing_unit") or "",
                "stock_status": row.get("stock_status") or "",
                "region": row.get("region") or "",
                "payment_tags": row.get("payment_tags") or "",
                "delivery_tags": row.get("delivery_tags") or "",
                "public_perf": row.get("public_perf") or "",
                "observed_at": row.get("observed_at") or "",
                "provenance": row.get("provenance") or "",
                "confidence": row.get("confidence"),
            }
        return rows

    def mark_staging(self, row_id: int, status: str) -> None:
        published_at = datetime.now(timezone.utc).replace(tzinfo=None) if status == "published" else None
        self._execute(
            "UPDATE collection_staging_observations SET publish_status = %s, published_at = %s WHERE id = %s",
            (status, published_at, row_id),
        )

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
