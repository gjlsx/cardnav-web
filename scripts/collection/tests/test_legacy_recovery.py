#!/usr/bin/env python3
"""Legacy direct-publish recovery only touches records with exact staging provenance."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.legacy_recovery import LegacyDirectPublishRecovery  # noqa: E402


class Repo:
    def __init__(self):
        self.backed_up = []
        self.deleted = []
        self.committed = False
        self.recovered_keys = set()

    def list_legacy_direct_published(self):
        rows = [
            {"record_kind": "shop_product", "record_key": "shop_product:known.example:chatgpt-plus", "source_id": "legacy-source", "payload": {"normalized_site": "known.example", "model_or_plan": "chatgpt-plus"}},
            {"record_kind": "shop_product", "record_key": "", "source_id": "legacy-source", "payload": {}},
            {"record_kind": "shop_product", "record_key": "shop_product:current.example:chatgpt-plus", "source_id": "current-source", "payload": {"normalized_site": "current.example", "model_or_plan": "chatgpt-plus"}},
        ]
        return [row for row in rows if row["record_key"] not in self.recovered_keys]

    def fetch_imported_raw_records(self):
        return [{
            "record_key": "shop_product:current.example:chatgpt-plus",
            "record_kind": "shop_product",
            "source_id": "current-source",
            "source_class": "site_api",
            "source_priority": 50,
            "validation_state": "valid",
            "payload": {
                "record_key": "shop_product:current.example:chatgpt-plus",
                "record_kind": "shop_product",
                "source_id": "current-source",
                "source_class": "site_api",
                "source_priority": 50,
                "normalized_site": "current.example",
                "model_or_plan": "chatgpt-plus",
                "price": 1,
            },
        }]

    def backup_legacy_candidate(self, recovery_id, candidate):
        self.backed_up.append((recovery_id, candidate["record_key"]))

    def delete_known_legacy_runtime(self, candidate):
        self.deleted.append(candidate["record_key"])
        return True

    def mark_legacy_candidate_recovered(self, candidate):
        self.recovered_keys.add(candidate["record_key"])

    def commit(self):
        self.committed = True

    def rollback(self):
        raise AssertionError("recovery should not roll back")


class Publisher:
    def __init__(self):
        self.kinds = []

    def rebuild_snapshots(self, _repository, kinds):
        self.kinds.append(kinds)


class LegacyRecoveryTests(unittest.TestCase):
    def test_diagnosis_leaves_ambiguous_rows_for_human_review(self):
        report = LegacyDirectPublishRecovery(Publisher()).diagnose(Repo())
        self.assertEqual(report["recoverable"], 1)
        self.assertEqual(report["ambiguous"], 2)

    def test_recovery_backs_up_and_deletes_only_exactly_identified_rows(self):
        repository = Repo()
        publisher = Publisher()
        result = LegacyDirectPublishRecovery(publisher).recover(repository, "recovery-1")
        self.assertEqual(result["recovered"], 1)
        self.assertEqual(result["ambiguous"], 2)
        self.assertEqual(repository.backed_up, [("recovery-1", "shop_product:known.example:chatgpt-plus")])
        self.assertEqual(repository.deleted, ["shop_product:known.example:chatgpt-plus"])
        self.assertTrue(repository.committed)
        self.assertEqual(len(publisher.kinds), 1)
        self.assertEqual(LegacyDirectPublishRecovery(publisher).diagnose(repository)["total"], 2)


if __name__ == "__main__":
    unittest.main()
