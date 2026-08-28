#!/usr/bin/env python3
"""Collection pipeline policy tests: raw is retained while locked rows are skipped."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib.pipeline import process_batch, run_source_pipeline  # noqa: E402


class MemoryRepository:
    def __init__(self, locked=()):
        self.locked = set(locked)
        self.raw_payloads = 0
        self.raw_records = []
        self.staging = []

    def write_raw_payload(self, *_args):
        self.raw_payloads += 1
        return self.raw_payloads

    def write_raw_record(self, _run, _source, key, _kind, payload, _payload_id):
        self.raw_records.append((key, payload))
        return len(self.raw_records)

    def has_manual_override(self, _kind, key):
        return key in self.locked

    def write_staging_record(self, record):
        self.staging.append(record)


class PipelineRepo(MemoryRepository):
    def __init__(self, locked=(), fail_publish=False):
        super().__init__(locked)
        self.fail_publish = fail_publish
        self.committed = False
        self.rolled_back = False
        self.finished = []

    def create_run(self, *_args):
        return None

    def finish_run(self, run_id, status, error=None):
        self.finished.append((run_id, status, error))

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        self.staging.clear()


class FakePublisher:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def publish_run(self, repository, run_id):
        if self.fail:
            raise RuntimeError("publish exploded")
        self.calls.append(run_id)
        return {"published": len(repository.staging)}


class PipelineTests(unittest.TestCase):
    def test_batch_retains_raw_but_skips_locked_product_from_staging(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository(locked=[key])
        rows = [
            {"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 10},
            {"normalized_site": "other.example.com", "model_or_plan": "claude-pro", "price": 20},
        ]
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", rows)
        self.assertEqual(result["raw_records"], 2)
        self.assertEqual(result["skipped_manual"], 1)
        self.assertEqual(len(repository.raw_records), 2)
        self.assertEqual(len(repository.staging), 1)

    def test_invalid_price_stays_out_of_staging(self):
        repository = MemoryRepository()
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": "bad"}])
        self.assertEqual(result["invalid"], 1)
        self.assertEqual(repository.staging, [])

    def test_hidden_override_is_skipped_like_manual_lock(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository(locked=[key])
        result = process_batch(repository, "run-1", "source-a", "application/json", "{}", [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 10}])
        self.assertEqual(result["skipped_manual"], 1)
        self.assertEqual(repository.staging, [])

    def test_publish_failure_rolls_back_and_does_not_commit_half_snapshot(self):
        from collection_lib.pipeline import run_source_pipeline

        repository = PipelineRepo()
        result = run_source_pipeline(
            repository,
            {"id": "source-a"},
            "{}",
            [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 9}],
            "application/json",
            "manual",
            RecordKind.SHOP_PRODUCT,
            FakePublisher(fail=True),
        )
        self.assertTrue(repository.rolled_back)
        self.assertEqual(result["published"]["published"], 0)
        self.assertIn("publish exploded", result["error"] or "")


class LiveMysqlHttpTests(unittest.TestCase):
    def test_approved_local_http_ingests_to_local_mysql(self):
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
            result = run_source_pipeline(repository, source, body, rows, content_type, "manual", RecordKind.SHOP_PRODUCT, PublicPublisher())
            self.assertIsNone(result["error"])
            self.assertGreaterEqual(result["published"]["published"], 1)
            stored = repository.query("SELECT standard_product, price_number FROM shop_products WHERE site_id = %s AND standard_product = %s", ("collected-p013-test.example", "chatgpt-plus"))
            self.assertEqual(len(stored), 1)
            self.assertEqual(float(stored[0]["price_number"]), 12.5)
            snap = repository.query("SELECT `key` FROM public_snapshot_entries WHERE `key` = 'shop-products'")
            self.assertEqual(len(snap), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            connection.close()


if __name__ == "__main__":
    unittest.main()
