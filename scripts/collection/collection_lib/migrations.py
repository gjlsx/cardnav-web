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
)

STAGING_COLUMNS = {
    "record_key": "VARCHAR(512) NOT NULL DEFAULT ''",
    "record_kind": "VARCHAR(32) NOT NULL DEFAULT ''",
    "quality_status": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
    "publish_status": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
    "raw_record_id": "BIGINT NULL",
    "published_at": "DATETIME NULL",
}

STAGING_INDEXES = {
    "collection_staging_record_key": "(record_key)",
    "collection_staging_publish_status": "(publish_status, quality_status)",
}


def apply_migrations(connection) -> None:
    """Create new tables and extend the one canonical staging table, never deleting data."""
    cursor = connection.cursor()
    try:
        for statement in CREATE_STATEMENTS:
            cursor.execute(statement)
        for name, definition in STAGING_COLUMNS.items():
            cursor.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() "
                "AND table_name = 'collection_staging_observations' AND column_name = %s LIMIT 1",
                (name,),
            )
            if cursor.fetchone() is None:
                cursor.execute(f"ALTER TABLE collection_staging_observations ADD COLUMN `{name}` {definition}")
        for name, definition in STAGING_INDEXES.items():
            cursor.execute(
                "SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() "
                "AND table_name = 'collection_staging_observations' AND index_name = %s LIMIT 1",
                (name,),
            )
            if cursor.fetchone() is None:
                cursor.execute(f"CREATE INDEX `{name}` ON collection_staging_observations {definition}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
