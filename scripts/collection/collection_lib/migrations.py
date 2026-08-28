"""Additive local MySQL schema migrations for the collection console."""
from __future__ import annotations


CREATE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS collection_sources (
      source_id VARCHAR(64) NOT NULL PRIMARY KEY,
      name VARCHAR(255) NOT NULL DEFAULT '', source_class VARCHAR(32) NOT NULL,
      target_domain VARCHAR(255) NOT NULL, priority INT NOT NULL DEFAULT 0,
      enabled BOOLEAN NOT NULL DEFAULT FALSE, interval_minutes INT NOT NULL DEFAULT 60,
      max_items_per_run INT NOT NULL DEFAULT 1000, approval_status VARCHAR(32) NOT NULL DEFAULT 'draft',
      field_whitelist JSON NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_runs (
      run_id VARCHAR(64) NOT NULL PRIMARY KEY, source_id VARCHAR(64) NOT NULL,
      trigger_type VARCHAR(32) NOT NULL, status VARCHAR(32) NOT NULL DEFAULT 'running',
      started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at DATETIME NULL,
      error_summary VARCHAR(500) NULL, KEY collection_runs_source_started (source_id, started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_batches (
      batch_id VARCHAR(64) NOT NULL PRIMARY KEY, trigger_type VARCHAR(32) NOT NULL,
      status VARCHAR(32) NOT NULL DEFAULT 'running', started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      finished_at DATETIME NULL, error_summary VARCHAR(500) NULL,
      KEY collection_batches_started (started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_raw_payloads (
      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, run_id VARCHAR(64) NOT NULL, source_id VARCHAR(64) NOT NULL,
      content_type VARCHAR(128) NOT NULL DEFAULT '', body_hash CHAR(64) NOT NULL, body LONGTEXT NULL,
      captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, body_expires_at DATETIME NOT NULL,
      KEY collection_raw_payloads_run (run_id), KEY collection_raw_payloads_expiry (body_expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_raw_records (
      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, run_id VARCHAR(64) NOT NULL, source_id VARCHAR(64) NOT NULL,
      record_key VARCHAR(512) NOT NULL, record_kind VARCHAR(32) NOT NULL, raw_payload_id BIGINT NULL,
      payload JSON NOT NULL, captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      KEY collection_raw_records_run (run_id), KEY collection_raw_records_key (record_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_manual_overrides (
      record_kind VARCHAR(32) NOT NULL, record_key VARCHAR(512) NOT NULL, state VARCHAR(32) NOT NULL,
      payload JSON NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (record_kind, record_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS console_activity_logs (
      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, page_key VARCHAR(100) NOT NULL, action VARCHAR(100) NOT NULL,
      message TEXT NOT NULL, details JSON NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      KEY console_activity_logs_page_created (page_key, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_legacy_recovery_backups (
      id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, recovery_id VARCHAR(80) NOT NULL,
      record_kind VARCHAR(32) NOT NULL, record_key VARCHAR(512) NOT NULL, source_id VARCHAR(64) NOT NULL,
      payload JSON NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      KEY collection_legacy_recovery_id (recovery_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
)

STAGING_COLUMNS = {
    "record_key": "VARCHAR(512) NOT NULL DEFAULT ''",
    "record_kind": "VARCHAR(32) NOT NULL DEFAULT ''",
    "quality_status": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
    "publish_status": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
    "raw_record_id": "BIGINT NULL",
    "published_at": "DATETIME NULL",
}

RUN_COLUMNS = {
    "batch_id": "VARCHAR(64) NULL",
}

RAW_RECORD_COLUMNS = {
    "batch_id": "VARCHAR(64) NULL",
    "source_class": "VARCHAR(32) NULL",
    "source_priority": "INT NULL",
    "source_url": "TEXT NULL",
    "source_record_hash": "VARCHAR(64) NULL",
    "validation_state": "VARCHAR(32) NOT NULL DEFAULT 'valid'",
    "validation_reason": "VARCHAR(500) NULL",
    "merged_at": "DATETIME NULL",
    "imported_at": "DATETIME NULL",
}

SOURCE_COLUMNS = {
    "public_url": "TEXT NULL",
    "allowlist_urls": "JSON NULL",
    "record_kind": "VARCHAR(32) NOT NULL DEFAULT 'shop_product'",
}

STAGING_INDEXES = {
    "collection_staging_record_key": "(record_key)",
    "collection_staging_publish_status": "(publish_status, quality_status)",
}

BATCH_INDEXES = {
    "collection_runs_batch": ("collection_runs", "(batch_id)"),
    "collection_raw_records_batch": ("collection_raw_records", "(batch_id)"),
    "collection_raw_records_batch_key": ("collection_raw_records", "(batch_id, record_key)"),
}


def apply_migrations(connection) -> None:
    """Create new tables and extend the one canonical staging table, never deleting data."""
    cursor = connection.cursor()
    try:
        for statement in CREATE_STATEMENTS:
            cursor.execute(statement)
        for table, columns in (
            ("collection_staging_observations", STAGING_COLUMNS),
            ("collection_sources", SOURCE_COLUMNS),
            ("collection_runs", RUN_COLUMNS),
            ("collection_raw_records", RAW_RECORD_COLUMNS),
        ):
            for name, definition in columns.items():
                cursor.execute(
                    "SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() "
                    "AND table_name = %s AND column_name = %s LIMIT 1",
                    (table, name),
                )
                if cursor.fetchone() is None:
                    cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{name}` {definition}")
        for name, definition in STAGING_INDEXES.items():
            cursor.execute(
                "SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() "
                "AND table_name = 'collection_staging_observations' AND index_name = %s LIMIT 1",
                (name,),
            )
            if cursor.fetchone() is None:
                cursor.execute(f"CREATE INDEX `{name}` ON collection_staging_observations {definition}")
        for name, (table, definition) in BATCH_INDEXES.items():
            cursor.execute(
                "SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() "
                "AND table_name = %s AND index_name = %s LIMIT 1",
                (table, name),
            )
            if cursor.fetchone() is None:
                cursor.execute(f"CREATE INDEX `{name}` ON `{table}` {definition}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
