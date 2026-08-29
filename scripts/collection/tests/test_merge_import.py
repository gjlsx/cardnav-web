#!/usr/bin/env python3
"""Explicit raw merge/import behavior and source-priority conflict resolution."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib.runtime_import import RuntimeImporter, merge_raw_records  # noqa: E402


def raw(source_id, source_class, priority, price, *, region=None, record_key="shop_product:shop.example.com:chatgpt-plus"):
    return {
        "record_key": record_key,
        "record_kind": RecordKind.SHOP_PRODUCT.value,
        "source_id": source_id,
        "source_class": source_class,
        "source_priority": priority,
        "validation_state": "valid",
        "payload": {
            "record_key": record_key,
            "record_kind": RecordKind.SHOP_PRODUCT.value,
            "source_id": source_id,
            "source_class": source_class,
            "source_priority": priority,
            "normalized_site": "shop.example.com",
            "model_or_plan": "chatgpt-plus",
            "price": price,
            "price_number": price,
            "currency": "CNY",
            "region": region,
        },
    }


class MemoryRepository:
    def __init__(self, rows, locked=(), latest_rows=None):
        self.batch = {"batch_id": "batch-1", "status": "raw_completed"}
        self.rows = rows
        self.latest_rows = latest_rows if latest_rows is not None else rows
        self.locked = set(locked)
        self.imported = []
        self.activity = []
        self.committed = False
        self.rolled_back = False

    def get_batch(self, batch_id):
        return self.batch if batch_id == "batch-1" else None

    def fetch_raw_batch(self, batch_id):
        return self.rows if batch_id == "batch-1" else []

    def fetch_latest_raw_for_keys(self, keys):
        return [row for row in self.latest_rows if row["record_key"] in keys]

    def has_manual_override(self, _kind, key):
        return key in self.locked

    def mark_batch_imported(self, batch_id):
        self.imported.append(batch_id)
        self.batch["status"] = "imported"

    def append_activity(self, *args):
        self.activity.append(args)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class RecordingPublisher:
    def __init__(self):
        self.rows = []
        self.snapshots = []

    def publish_merged_row(self, _repository, row):
        self.rows.append(row)

    def rebuild_snapshots(self, _repository, kinds):
        self.snapshots.append(kinds)


class FailingPublisher(RecordingPublisher):
    def publish_merged_row(self, _repository, _row):
        raise RuntimeError("runtime write failed")


class MergeRawTests(unittest.TestCase):
    def test_priority_winner_keeps_lower_priority_region_only_as_a_fill(self):
        merged = merge_raw_records([
            raw("own-api", "site_api", 50, 10),
            raw("openprice-products", "aggregator", 10, 1, region="CN"),
        ])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["payload"]["source_id"], "own-api")
        self.assertEqual(merged[0]["payload"]["price_number"], 10)
        self.assertEqual(merged[0]["payload"]["region"], "CN")

    def test_same_priority_uses_lowest_price(self):
        merged = merge_raw_records([
            raw("priceai-a", "aggregator", 30, 10),
            raw("priceai-b", "aggregator", 30, 5),
        ])
        self.assertEqual(merged[0]["payload"]["source_id"], "priceai-b")
        self.assertEqual(merged[0]["payload"]["price_number"], 5)


class RuntimeImportTests(unittest.TestCase):
    def test_explicit_merge_import_writes_one_runtime_winner_and_is_idempotent(self):
        repository = MemoryRepository([raw("priceai-channels", "aggregator", 30, 9), raw("cardnav-home", "aggregator", 20, 8)])
        publisher = RecordingPublisher()
        importer = RuntimeImporter(publisher)

        result = importer.merge_import_batch(repository, "batch-1")

        self.assertEqual(result["runtime_writes"], 1)
        self.assertEqual(publisher.rows[0]["payload"]["source_id"], "priceai-channels")
        self.assertEqual(repository.imported, ["batch-1"])
        self.assertTrue(repository.committed)
        retry = importer.merge_import_batch(repository, "batch-1")
        self.assertEqual(retry["runtime_writes"], 0)
        self.assertEqual(len(publisher.rows), 1)

    def test_lock_added_after_raw_collection_skips_runtime_write(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        repository = MemoryRepository([raw("priceai-channels", "aggregator", 30, 9, record_key=key)], locked=[key])
        publisher = RecordingPublisher()

        result = RuntimeImporter(publisher).merge_import_batch(repository, "batch-1")

        self.assertEqual(result["runtime_writes"], 0)
        self.assertEqual(result["skipped_manual"], 1)
        self.assertEqual(publisher.rows, [])
        self.assertEqual(len(repository.rows), 1)

    def test_later_low_priority_single_source_batch_keeps_latest_high_priority_raw_winner(self):
        key = "shop_product:shop.example.com:chatgpt-plus"
        low_only_batch = raw("openprice-products", "aggregator", 10, 1, record_key=key)
        latest_high = raw("priceai-channels", "aggregator", 30, 9, record_key=key)
        repository = MemoryRepository([low_only_batch], latest_rows=[low_only_batch, latest_high])
        publisher = RecordingPublisher()

        RuntimeImporter(publisher).merge_import_batch(repository, "batch-1")

        self.assertEqual(publisher.rows[0]["source_id"], "priceai-channels")
        self.assertEqual(publisher.rows[0]["payload"]["price_number"], 9)

    def test_failed_runtime_write_rolls_back_without_marking_batch_imported(self):
        repository = MemoryRepository([raw("priceai-channels", "aggregator", 30, 9)])

        with self.assertRaisesRegex(RuntimeError, "runtime write failed"):
            RuntimeImporter(FailingPublisher()).merge_import_batch(repository, "batch-1")

        self.assertTrue(repository.rolled_back)
        self.assertEqual(repository.imported, [])
        self.assertEqual(repository.batch["status"], "raw_completed")


if __name__ == "__main__":
    unittest.main()
