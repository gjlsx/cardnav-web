from __future__ import annotations

import json
import unittest

from scripts.collection.collection_lib.contracts import RecordKind
from scripts.collection.collection_lib.publisher import PublicPublisher
from scripts.collection.collection_lib.pipeline import normalize_raw_observation
from scripts.crawlee_collection.parser import parse_hvoyai_reference_json
from scripts.crawlee_collection.sources import get_source


FIXTURE = json.dumps({
    "updatedDate": "2026-08-30",
    "generatedAt": "2026-08-30T00:10:05.000Z",
    "sites": [
        {
            "rank": 2,
            "name": "Beta API",
            "url": "https://www.hvoyai.com/sites/beta-api/",
            "modelCount": 12,
            "models": ["OpenAI", "DeepSeek"],
            "uptime": 99.2,
            "latencyMs": 820,
            "userRating": 4.5,
            "ratingCount": 8,
            "paymentMethods": ["微信"],
            "supportsRefund": True,
            "supportsInvoice": False,
        },
        {
            "rank": 1,
            "name": "Alpha API",
            "url": "https://www.hvoyai.com/sites/alpha-api/",
            "modelCount": 20,
            "models": ["OpenAI"],
            "uptime": None,
            "latencyMs": None,
            "userRating": None,
            "ratingCount": 0,
            "paymentMethods": [],
            "supportsRefund": None,
            "supportsInvoice": None,
        },
        {
            "rank": 3,
            "name": "Duplicate Alpha",
            "url": "https://www.hvoyai.com/sites/alpha-api/",
        },
        {
            "rank": 4,
            "name": "Not a Hvoy detail URL",
            "url": "https://merchant.example/",
        },
    ],
}, ensure_ascii=False)


class _SnapshotRepository:
    def __init__(self) -> None:
        self.snapshots: dict[str, object] = {}

    def upsert_snapshot(self, key: str, payload: object) -> None:
        self.snapshots[key] = payload


class HvoyaiReferenceTests(unittest.TestCase):
    def test_parser_keeps_only_unique_hvoy_detail_records_and_nullable_fields(self) -> None:
        capture = parse_hvoyai_reference_json(
            get_source("hvoyai-awesome-ai-api"),
            FIXTURE,
            observed_at="2026-08-30T01:00:00Z",
        )

        self.assertEqual(capture.content_type, "application/json")
        self.assertEqual(capture.kind, RecordKind.GATEWAY_SITE)
        self.assertEqual([row["site_name"] for row in capture.rows], ["Beta API", "Alpha API"])
        beta = capture.rows[0]
        self.assertEqual(beta["normalized_site"], "hvoyai-reference-beta-api.invalid")
        self.assertEqual(beta["metadata_json"]["source_rank"], 2)
        self.assertEqual(beta["metadata_json"]["user_rating"], 4.5)
        self.assertEqual(capture.rows[1]["metadata_json"]["uptime"], None)

    def test_raw_record_uses_an_opaque_reference_key_not_a_gateway_site_host(self) -> None:
        row = parse_hvoyai_reference_json(
            get_source("hvoyai-awesome-ai-api"), FIXTURE, observed_at="2026-08-30T01:00:00Z"
        ).rows[0]
        key, payload, state, _ = normalize_raw_observation(
            row,
            {"id": "hvoyai-awesome-ai-api", "source_class": "reference", "public_url": get_source("hvoyai-awesome-ai-api").url},
            RecordKind.GATEWAY_SITE,
            batch_id="batch-1",
            run_id="run-1",
        )

        self.assertEqual((key, state), ("gateway_site:hvoyai-reference-beta-api.invalid", "valid"))
        self.assertEqual(payload["metadata_json"]["source_rank"], 2)

    def test_public_reference_snapshot_is_sorted_by_upstream_rank_and_has_no_aigate_score(self) -> None:
        capture = parse_hvoyai_reference_json(
            get_source("hvoyai-awesome-ai-api"), FIXTURE, observed_at="2026-08-30T01:00:00Z"
        )
        repository = _SnapshotRepository()

        PublicPublisher().rebuild_gateway_reference_snapshot(repository, [
            {"source_id": "hvoyai-awesome-ai-api", "payload": row} for row in capture.rows
        ])

        snapshot = repository.snapshots["gateway-reference-ranking"]
        self.assertEqual([item["name"] for item in snapshot["sites"]], ["Alpha API", "Beta API"])
        self.assertEqual(snapshot["sites"][0]["sourceRank"], 1)
        self.assertNotIn("siteScore", snapshot["sites"][0])
        self.assertEqual(snapshot["sourceUpdatedAt"], "2026-08-30T00:10:05.000Z")


if __name__ == "__main__":
    unittest.main()
