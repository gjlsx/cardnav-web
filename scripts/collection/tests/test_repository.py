#!/usr/bin/env python3
"""Persistence contracts: additive migrations and parameterized repository writes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import OverrideState, RecordKind  # noqa: E402
from collection_lib.migrations import CREATE_STATEMENTS, apply_migrations  # noqa: E402
from collection_lib.repository import CollectionRepository  # noqa: E402
from collection_lib.staging import ensure_staging_table  # noqa: E402
from collect import cmd_migrate  # noqa: E402


class FakeCursor:
    def __init__(self, rows=None):
        self.calls = []
        self.rows = rows or []
        self.lastrowid = 17

    def execute(self, sql, params=()):
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def close(self):
        return None


class FakeConnection:
    def __init__(self, rows=None):
        self.cursor_instance = FakeCursor(rows)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class MigrationTests(unittest.TestCase):
    def test_schema_uses_mysql_57_portable_timestamp_defaults(self):
        schema = "\n".join(CREATE_STATEMENTS).upper()
        self.assertNotIn("DATETIME NOT NULL DEFAULT UTC_TIMESTAMP()", schema)
        self.assertIn("TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP", schema)

    def test_migration_extends_existing_observations_without_second_staging_table(self):
        connection = FakeConnection()
        apply_migrations(connection)
        sql = "\n".join(call[0] for call in connection.cursor_instance.calls)
        self.assertIn("CREATE TABLE IF NOT EXISTS collection_sources", sql)
        self.assertIn("ALTER TABLE `collection_staging_observations` ADD COLUMN `record_key`", sql)
        self.assertNotIn("collection_staging_records", sql)
        self.assertNotIn(" DROP ", sql.upper())
        self.assertEqual(connection.commits, 1)


class RepositoryTests(unittest.TestCase):
    def test_raw_and_override_writes_are_parameterized(self):
        connection = FakeConnection()
        repository = CollectionRepository(connection)
        repository.create_run("run-1", "source-a", "manual")
        payload_body = "{\"x\":\"quote'\"}"
        payload_id = repository.write_raw_payload("run-1", "source-a", "application/json", "h1", payload_body)
        repository.write_raw_record("run-1", "source-a", "gateway_site:api.example.com", RecordKind.GATEWAY_SITE, {"name": "A"}, payload_id)
        repository.set_manual_override(RecordKind.GATEWAY_SITE, "gateway_site:api.example.com", OverrideState.MANUAL, {"name": "manual"})
        calls = connection.cursor_instance.calls
        joined = "\n".join(call[0] for call in calls)
        self.assertIn("INSERT INTO collection_raw_payloads", joined)
        self.assertIn("INSERT INTO collection_manual_overrides", joined)
        self.assertNotIn("quote", joined)
        self.assertEqual(calls[1][1][-2], payload_body)

    def test_purge_only_nulls_expired_body_and_retains_audit_rows(self):
        connection = FakeConnection()
        repository = CollectionRepository(connection)
        repository.purge_expired_payload_bodies()
        sql, params = connection.cursor_instance.calls[-1]
        self.assertIn("SET body = NULL", sql)
        self.assertIn("body_expires_at < UTC_TIMESTAMP()", sql)
        self.assertEqual(params, ())


class CliTests(unittest.TestCase):
    def test_migrate_uses_one_local_connection_and_closes_it(self):
        connection = FakeConnection()
        with patch("collect.open_local_connection", return_value=connection), patch("collect.apply_migrations") as migrate:
            self.assertEqual(cmd_migrate(), 0)
        migrate.assert_called_once_with(connection)
        self.assertEqual(connection.commits, 0)
        self.assertTrue(connection.closed)


class LegacyStagingTests(unittest.TestCase):
    def test_existing_staging_entry_runs_additive_migration(self):
        connection = FakeConnection()
        with patch("collection_lib.staging.run_mysql") as legacy_create, patch("collection_lib.staging.open_local_connection", return_value=connection), patch("collection_lib.staging.apply_migrations") as migrate:
            ensure_staging_table()
        legacy_create.assert_called_once()
        migrate.assert_called_once_with(connection)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
