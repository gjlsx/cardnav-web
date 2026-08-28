#!/usr/bin/env python3
"""Collection pipeline policy tests: raw is retained while locked rows are skipped."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.pipeline import process_batch  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
