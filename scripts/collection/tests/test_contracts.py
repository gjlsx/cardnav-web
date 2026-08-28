#!/usr/bin/env python3
"""Contract tests for the local collection pipeline."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import (  # noqa: E402
    CollectionRun,
    ManualOverride,
    OverrideState,
    RawPayload,
    RawRecord,
    RecordKind,
    SourceConfig,
    StagingRecord,
    normalize_host,
    record_key,
)


class RecordKeyTests(unittest.TestCase):
    def test_normalizes_hosts_and_builds_each_stable_key(self):
        self.assertEqual(normalize_host("HTTPS://Shop.Example.com:443/a/"), "shop.example.com")
        self.assertEqual(
            record_key(RecordKind.SHOP_PRODUCT, host="Shop.Example.com", canonical_sku=" ChatGPT Plus "),
            "shop_product:shop.example.com:chatgpt-plus",
        )
        self.assertEqual(
            record_key(RecordKind.GATEWAY_SITE, host="https://API.Example.com/v1"),
            "gateway_site:api.example.com",
        )
        self.assertEqual(
            record_key(RecordKind.OFFICIAL_PLAN, plan_slug="ChatGPT Plus", country_code="us"),
            "official_plan:chatgpt-plus:US",
        )
        self.assertEqual(
            record_key(RecordKind.MODEL_RANK, task_slug="Text Generation", model_name="GPT 5"),
            "model_rank:text-generation:gpt-5",
        )

    def test_rejects_missing_identity_parts(self):
        with self.assertRaises(ValueError):
            record_key(RecordKind.SHOP_PRODUCT, host="shop.example.com", canonical_sku="")


class ContractTests(unittest.TestCase):
    def test_source_priority_has_no_site_score(self):
        source = SourceConfig(
            source_id="source-a",
            name="Source A",
            source_class="site_api",
            target_domain="api.example.com",
            priority=70,
        )
        self.assertEqual(source.priority, 70)
        self.assertFalse(hasattr(source, "score"))
        with self.assertRaises(TypeError):
            SourceConfig("source-b", "Source B", "site_html", "example.com", score=50)

    def test_pipeline_records_are_immutable(self):
        run = CollectionRun(run_id="run-1", source_id="source-a", trigger="manual")
        payload = RawPayload(run_id="run-1", source_id="source-a", body_hash="hash", content_type="application/json")
        raw = RawRecord(run_id="run-1", source_id="source-a", record_key="gateway_site:api.example.com", payload={"name": "A"})
        staging = StagingRecord(run_id="run-1", record_kind=RecordKind.GATEWAY_SITE, record_key=raw.record_key, payload={"name": "A"})
        override = ManualOverride(record_kind=RecordKind.GATEWAY_SITE, record_key=raw.record_key, state=OverrideState.MANUAL)
        self.assertEqual((run.run_id, payload.body_hash, raw.record_key, staging.record_kind, override.state), ("run-1", "hash", raw.record_key, RecordKind.GATEWAY_SITE, OverrideState.MANUAL))
        with self.assertRaises(FrozenInstanceError):
            run.trigger = "scheduler"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
