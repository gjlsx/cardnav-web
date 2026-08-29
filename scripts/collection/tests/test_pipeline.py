#!/usr/bin/env python3
"""Collection pipeline policy tests: raw is retained and runtime import is separate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib.pipeline import process_batch, run_source_pipeline  # noqa: E402
from collection_lib.publisher import PublicPublisher  # noqa: E402


class MemoryRepository:
    def __init__(self, locked=()):
        self.locked = set(locked)
        self.raw_payloads = 0
        self.raw_records = []
        self.staging = []

    def write_raw_payload(self, *_args):
        self.raw_payloads += 1
        return self.raw_payloads

    def write_raw_record(self, _run, _source, key, _kind, payload, _payload_id, **_kwargs):
        self.raw_records.append((key, payload))
        return len(self.raw_records)

    def has_manual_override(self, _kind, key):
        return key in self.locked

class PipelineRepo(MemoryRepository):
    def __init__(self, locked=(), fail_publish=False):
        super().__init__(locked)
        self.fail_publish = fail_publish
        self.committed = False
        self.rolled_back = False
        self.finished = []
        self.batches = []

    def create_batch(self, batch_id, trigger):
        self.batches.append((batch_id, trigger, "running"))

    def finish_batch(self, batch_id, status, error=None):
        self.batches.append((batch_id, status, error))

    def create_run(self, *_args):
        return None

    def finish_run(self, run_id, status, error=None):
        self.finished.append((run_id, status, error))

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        self.staging.clear()


class PipelineTests(unittest.TestCase):
    def test_batch_retains_raw_for_locked_product_without_staging(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository(locked=[key])
        rows = [
            {"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 10},
            {"normalized_site": "other.example.com", "model_or_plan": "claude-pro", "price": 20},
        ]
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", rows)
        self.assertEqual(result["raw_records"], 2)
        self.assertEqual(result["manual_marked"], 1)
        self.assertEqual(len(repository.raw_records), 2)
        self.assertEqual(len(repository.staging), 0)

    def test_invalid_price_is_retained_as_invalid_raw(self):
        repository = MemoryRepository()
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": "bad"}])
        self.assertEqual(result["invalid"], 0)
        self.assertEqual(len(repository.raw_records), 1)
        self.assertEqual(repository.staging, [])

    def test_hidden_override_is_marked_but_retained_in_raw(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository(locked=[key])
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 10}])
        self.assertEqual(result["manual_marked"], 1)
        self.assertEqual(len(repository.raw_records), 1)
        self.assertEqual(repository.staging, [])

    def test_stop_flag_creates_no_runtime_writes(self):
        repository = PipelineRepo()
        result = run_source_pipeline(
            repository, {"id": "stop-source"}, "[]",
            [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 9}],
            "application/json", "manual", RecordKind.SHOP_PRODUCT, should_stop=lambda: True,
        )
        self.assertTrue(result["stopped"])
        self.assertEqual(result["published"]["published"], 0)
        self.assertEqual(result["runtime_writes"], 0)
        self.assertEqual(repository.staging, [])

    def test_source_capture_finishes_as_raw_completed_without_a_publisher(self):
        repository = PipelineRepo()
        result = run_source_pipeline(
            repository, {"id": "source-a"}, "{}",
            [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 9}],
            "application/json", "manual", RecordKind.SHOP_PRODUCT,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["runtime_writes"], 0)
        self.assertTrue(repository.committed)
        self.assertIn("raw_completed", [row[1] for row in repository.batches])


class LiveMysqlHttpTests(unittest.TestCase):
    @staticmethod
    def _purge_live_fixture(repository):
        source_id = "p013-http"
        site_id = "collected-p013-test.example"
        repository.execute("DELETE FROM collection_staging_observations WHERE source_id = %s", (source_id,))
        repository.execute("DELETE FROM collection_raw_records WHERE source_id = %s", (source_id,))
        repository.execute("DELETE FROM collection_raw_payloads WHERE source_id = %s", (source_id,))
        repository.execute("DELETE FROM collection_runs WHERE source_id = %s", (source_id,))
        repository.execute("DELETE FROM shop_products WHERE site_id = %s", (site_id,))
        repository.execute("DELETE FROM shop_sites WHERE id = %s AND NOT EXISTS (SELECT 1 FROM shop_products WHERE shop_products.site_id = %s)", (site_id, site_id))
        PublicPublisher().rebuild_snapshots(repository, {RecordKind.SHOP_PRODUCT})
        repository.commit()

    def test_live_http_fixture_does_not_leave_publishable_test_site(self):
        from collect import load_dotenv
        from collection_lib.repository import CollectionRepository, open_local_connection

        load_dotenv()
        connection = open_local_connection()
        try:
            repository = CollectionRepository(connection)
            rows = repository.query("SELECT 1 FROM shop_products WHERE site_id = %s LIMIT 1", ("collected-p013-test.example",))
            self.assertEqual(rows, [])
        finally:
            connection.close()

    def test_approved_local_http_ingests_raw_only_to_local_mysql(self):
        import json
        import os
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from collect import load_dotenv
        from collection_lib.migrations import apply_migrations
        from collection_lib.publisher import PublicPublisher
        from collection_lib.repository import CollectionRepository, open_local_connection

        load_dotenv()
        try:
            connection = open_local_connection()
        except Exception as exc:  # noqa: BLE001
            self.skipTest(str(exc))

        payload = [{"normalized_site": "p013-test.example", "model_or_plan": "chatgpt-plus", "price": 12.5, "currency": "CNY"}]

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_address[1]}/data"
        try:
            apply_migrations(connection)
            repository = CollectionRepository(connection)
            from collection_lib.fetch import fetch_approved_json
            source = {"id": "p013-http", "approval_status": "approved", "allowlist_urls": [url], "public_url": url, "record_kind": "shop_product"}
            body, rows, content_type = fetch_approved_json(source)
            result = run_source_pipeline(repository, source, body, rows, content_type, "manual", RecordKind.SHOP_PRODUCT)
            self.assertIsNone(result["error"])
            self.assertEqual(result["runtime_writes"], 0)
            stored = repository.query("SELECT standard_product, price_number FROM shop_products WHERE site_id = %s AND standard_product = %s", ("collected-p013-test.example", "chatgpt-plus"))
            self.assertEqual(stored, [])
            raw = repository.query("SELECT batch_id, validation_state FROM collection_raw_records WHERE source_id = %s", ("p013-http",))
            self.assertEqual(len(raw), 1)
            self.assertTrue(raw[0]["batch_id"])
            self.assertEqual(raw[0]["validation_state"], "valid")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            self._purge_live_fixture(CollectionRepository(connection))
            connection.close()


if __name__ == "__main__":
    unittest.main()
