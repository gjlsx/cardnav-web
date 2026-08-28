#!/usr/bin/env python3
"""Unified raw batch behavior: capture retains raw and does not publish."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib.pipeline import SourceCapture, process_batch, run_collection_batch  # noqa: E402


class MemoryRepository:
    def __init__(self, locked=()):
        self.locked = set(locked)
        self.batches = []
        self.runs = []
        self.raw_payloads = []
        self.raw_records = []
        self.staging = []
        self.committed = False

    def create_batch(self, batch_id, trigger):
        self.batches.append((batch_id, trigger, "running"))

    def finish_batch(self, batch_id, status, error_summary=None):
        self.batches.append((batch_id, status, error_summary))

    def create_run(self, run_id, source_id, trigger, batch_id=None):
        self.runs.append((run_id, source_id, trigger, batch_id))

    def finish_run(self, *_args):
        return None

    def write_raw_payload(self, *args):
        self.raw_payloads.append(args)
        return len(self.raw_payloads)

    def write_raw_record(self, *args, **kwargs):
        self.raw_records.append((args, kwargs))
        return len(self.raw_records)

    def has_manual_override(self, _kind, key):
        return key in self.locked

    def write_staging_record(self, record):
        self.staging.append(record)

    def commit(self):
        self.committed = True

    def rollback(self):
        return None


class UnifiedRawBatchTests(unittest.TestCase):
    def test_process_batch_retains_a_locked_record_as_unified_raw_without_staging(self):
        locked_key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository(locked=[locked_key])

        result = process_batch(
            repository,
            "run-1",
            "priceai-channels",
            "application/json",
            "[]",
            [{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 8, "channel_count": 6}],
            source={"id": "priceai-channels", "source_class": "aggregator", "priority": 30, "public_url": "https://priceai.cc/channels"},
        )

        self.assertEqual(result["raw_records"], 1)
        self.assertEqual(result["manual_marked"], 1)
        self.assertEqual(repository.staging, [])
        args, _kwargs = repository.raw_records[0]
        payload = args[4]
        self.assertEqual(payload["source_id"], "priceai-channels")
        self.assertEqual(payload["source_class"], "aggregator")
        self.assertEqual(payload["canonical_site"], "shop.example.com")
        self.assertEqual(payload["canonical_sku"], "chatgpt-plus")
        self.assertEqual(payload["channel_count"], 6)
        self.assertEqual(payload["validation_state"], "valid")

    def test_two_sources_share_one_batch_and_only_persist_sparse_raw_records(self):
        repository = MemoryRepository()
        result = run_collection_batch(
            repository,
            [
                SourceCapture(
                    source={"id": "site-api", "source_class": "site_api", "priority": 50, "public_url": "https://api.example.com/models"},
                    body="[]",
                    rows=[{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 10, "currency": "CNY"}],
                    content_type="application/json",
                    kind=RecordKind.SHOP_PRODUCT,
                ),
                SourceCapture(
                    source={"id": "openprice-products", "source_class": "aggregator", "priority": 10, "public_url": "https://openprice.cc/card-products"},
                    body="[]",
                    rows=[{"normalized_site": "shop.example.com", "model_or_plan": "chatgpt-plus", "price": 5, "region": "CN"}],
                    content_type="application/json",
                    kind=RecordKind.SHOP_PRODUCT,
                ),
            ],
            trigger="manual",
            batch_id="batch-raw-1",
        )

        self.assertEqual(result["batch_id"], "batch-raw-1")
        self.assertEqual({run[3] for run in repository.runs}, {"batch-raw-1"})
        self.assertEqual(len(repository.raw_records), 2)
        self.assertEqual(repository.staging, [])
        self.assertEqual(result["runtime_writes"], 0)
        self.assertTrue(repository.committed)
        sparse_payload = repository.raw_records[1][0][4]
        self.assertEqual(sparse_payload["currency"], None)
        self.assertEqual(sparse_payload["region"], "CN")
        self.assertEqual(sparse_payload["source_id"], "openprice-products")


if __name__ == "__main__":
    unittest.main()
