from __future__ import annotations

import unittest

from scripts.collection.collection_lib.publisher import PublicPublisher
from scripts.collection.collection_lib.contracts import RecordKind
from scripts.collection.collection_lib.pipeline import normalize_raw_observation
from scripts.crawlee_collection.gateway import (
    GatewayListing,
    build_cardnav_captures,
    discover_gateway_listings,
    normalize_gateway_model_id,
    parse_cardnav_gateway_detail,
    parse_priceai_standard_models,
)


PRICEAI_MODELS_HTML = """
<table><tbody>
  <tr><td>GPT   5.6 Luna<span>ChatGPT · 13 个站点</span></td></tr>
  <tr><td>Claude Sonnet 4.6<span>Claude · 14 个站点</span></td></tr>
</tbody></table>
"""

CARDNAV_LIST_HTML = """
<table><tbody><tr>
  <td>1</td>
  <td><a href="/llm-gateway/linkai">LinkAi</a><p>稳定的统一入口</p><a href="https://linkai.shop">打开</a></td>
  <td>263.21</td><td>GPT</td><td>2</td>
</tr></tbody></table>
<a href="/llm-gateway/models/gpt-5.6-luna">模型页不是详情</a>
<a href="https://merchant.example/llm-gateway/nope">外部链接</a>
"""

CARDNAV_DETAIL_HTML = """
<h1>LinkAi</h1>
<meta name="description" content="一个统一 API 入口">
<table><tbody>
  <tr><td>1</td><td>GPT  5.6   Luna</td><td>$ / 1M tokens</td><td>2.5</td><td>15</td><td>0.25</td><td>-</td></tr>
  <tr><td>2</td><td>Other Model</td><td>$ / 1M tokens</td><td>1</td><td>2</td><td>-</td><td>-</td></tr>
</tbody></table>
"""


class _RecordingRepository:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple]] = []
        self.snapshots: dict[str, object] = {}

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.executed.append((sql, params))

    def query(self, sql: str, params: tuple = ()):  # noqa: ANN001, ANN201
        return []

    def upsert_snapshot(self, key: str, payload: object) -> None:
        self.snapshots[key] = payload

    def hidden_keys(self, kind: str) -> set[str]:
        return set()


class CardNavGatewayParserTests(unittest.TestCase):
    def test_standard_model_id_casefolds_and_collapses_spaces(self) -> None:
        self.assertEqual(normalize_gateway_model_id("  GPT   5.6  Luna  "), "gpt-5.6-luna")

    def test_priceai_catalog_is_the_only_allowed_model_set(self) -> None:
        self.assertEqual(
            parse_priceai_standard_models(PRICEAI_MODELS_HTML),
            {"gpt-5.6-luna", "claude-sonnet-4.6"},
        )

    def test_cardnav_list_discovers_only_same_origin_site_detail_links(self) -> None:
        listings = discover_gateway_listings(CARDNAV_LIST_HTML)

        self.assertEqual(listings, [
            GatewayListing(
                slug="linkai",
                detail_url="https://cardnav.xyz/llm-gateway/linkai",
                host="linkai.shop",
                name="LinkAi",
                summary="稳定的统一入口",
                score=263.21,
            )
        ])

    def test_detail_keeps_only_priceai_models_and_keeps_price_columns(self) -> None:
        listing = GatewayListing("linkai", "https://cardnav.xyz/llm-gateway/linkai", "linkai.shop", "LinkAi", "", 0)
        row = parse_cardnav_gateway_detail(
            listing,
            CARDNAV_DETAIL_HTML,
            allowed_models={"gpt-5.6-luna"},
            observed_at="2026-08-30T00:00:00Z",
        )

        self.assertEqual(row["normalized_site"], "linkai.shop")
        self.assertEqual(row["metadata_json"]["models"], [{
            "model_id": "gpt-5.6-luna",
            "model_family": "GPT",
            "billing_unit": "$ / 1M tokens",
            "input_price": 2.5,
            "output_price": 15.0,
            "cache_input_price": 0.25,
            "cache_output_price": None,
        }])

    def test_capture_builder_keeps_catalog_raw_but_only_detail_rows_publishable(self) -> None:
        from scripts.crawlee_collection.sources import get_source

        captures = build_cardnav_captures(
            get_source("priceai-transit-models"),
            PRICEAI_MODELS_HTML,
            get_source("cardnav-gateway-details"),
            CARDNAV_LIST_HTML,
            {"https://cardnav.xyz/llm-gateway/linkai": CARDNAV_DETAIL_HTML},
            observed_at="2026-08-30T00:00:00Z",
        )

        self.assertEqual([capture.source["id"] for capture in captures], [
            "priceai-transit-models", "cardnav-gateway-details", "cardnav-gateway-details",
        ])
        self.assertEqual(captures[0].rows, [])
        self.assertEqual(captures[-1].rows[0]["metadata_json"]["models"][0]["model_id"], "gpt-5.6-luna")

    def test_gateway_publisher_writes_all_approved_coverage_and_prices(self) -> None:
        repository = _RecordingRepository()
        row = {
            "record_kind": "gateway_site",
            "source_id": "cardnav-gateway-details",
            "payload": {
                "normalized_site": "linkai.shop",
                "site_name": "LinkAi",
                "observed_at": "2026-08-30T00:00:00Z",
                "metadata_json": {"models": [{
                    "model_id": "gpt-5.6-luna", "model_family": "GPT", "billing_unit": "$ / 1M tokens",
                    "input_price": 2.5, "output_price": 15.0, "cache_input_price": 0.25, "cache_output_price": None,
                }]},
            },
        }

        publisher = PublicPublisher()
        publisher.publish_merged_row(repository, row)
        publisher.rebuild_snapshots(repository, {RecordKind.GATEWAY_SITE})

        statements = "\n".join(sql for sql, _ in repository.executed)
        self.assertIn("gateway_model_coverage", statements)
        self.assertIn("gateway_model_prices", statements)
        self.assertIn("gateway-sites", repository.snapshots)
        self.assertIn("gateway-models", repository.snapshots)

    def test_raw_pipeline_keeps_gateway_model_metadata_for_merge(self) -> None:
        key, payload, state, _ = normalize_raw_observation(
            {"normalized_site": "linkai.shop", "metadata_json": {"models": [{"model_id": "gpt-5.6-luna"}]}},
            {"id": "cardnav-gateway-details", "public_url": "https://cardnav.xyz/llm-gateway"},
            RecordKind.GATEWAY_SITE,
            batch_id="batch-1",
            run_id="run-1",
        )

        self.assertEqual((key, state), ("gateway_site:linkai.shop", "valid"))
        self.assertEqual(payload["metadata_json"]["models"][0]["model_id"], "gpt-5.6-luna")


if __name__ == "__main__":
    unittest.main()
