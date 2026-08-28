"""Parameterized MySQL persistence for local collection runs."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pymysql

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

    def purge_expired_payload_bodies(self) -> None:
        self._execute("UPDATE collection_raw_payloads SET body = NULL WHERE body_expires_at < UTC_TIMESTAMP() AND body IS NOT NULL")

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()
