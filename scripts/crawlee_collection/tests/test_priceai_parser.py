from __future__ import annotations

import unittest

from scripts.collection.collection_lib.pipeline import normalize_raw_observation
from scripts.crawlee_collection.parser import parse_priceai_page
from scripts.crawlee_collection.sources import get_source


class PriceAiParserTests(unittest.TestCase):
    def test_channels_maps_merchant_card_to_existing_shop_product_contract(self) -> None:
        capture = parse_priceai_page(
            get_source("priceai-card-subscriptions"),
            """
            <article data-collection-card="shop">
              <a href="https://cc-cat.example/products/gemini-pro"><span>cc-cat</span></a>
              <h3>Gemini Pro 月卡</h3><span>¥29.90</span><span>有货</span>
            </article>
            """,
            observed_at="2026-08-29T14:57:00Z",
        )

        self.assertEqual(capture.kind.value, "shop_product")
        self.assertEqual(capture.rows[0]["normalized_site"], "cc-cat.example")
        self.assertEqual(capture.rows[0]["canonical_sku"], "gemini-pro")
        self.assertEqual(capture.rows[0]["price"], 29.9)
        key, _, state, _ = normalize_raw_observation(capture.rows[0], capture.source, capture.kind, batch_id="b", run_id="r")
        self.assertEqual(key, "shop_product:cc-cat.example:gemini-pro")
        self.assertEqual(state, "valid")

    def test_official_page_maps_plan_and_country_to_existing_official_contract(self) -> None:
        capture = parse_priceai_page(
            get_source("priceai-official-api"),
            """
            <article data-collection-card="official" data-country="US">
              <h3>ChatGPT Plus</h3><span>$20</span><span>美国</span>
            </article>
            """,
            observed_at="2026-08-29T14:57:00Z",
        )

        self.assertEqual(capture.kind.value, "official_plan")
        self.assertEqual(capture.rows[0]["plan_slug"], "chatgpt-plus")
        self.assertEqual(capture.rows[0]["country_code"], "US")
        key, _, state, _ = normalize_raw_observation(capture.rows[0], capture.source, capture.kind, batch_id="b", run_id="r")
        self.assertEqual(key, "official_plan:chatgpt-plus:US")
        self.assertEqual(state, "valid")

    def test_transit_page_maps_gateway_card_to_existing_gateway_contract(self) -> None:
        capture = parse_priceai_page(
            get_source("priceai-transit-api"),
            """
            <article data-collection-card="gateway">
              <a href="https://api.cat.example/v1"><h3>Cat Gateway</h3></a>
              <p>支持 GPT、Claude</p><span>￥0.50 / 1M tokens</span>
            </article>
            """,
            observed_at="2026-08-29T14:57:00Z",
        )

        self.assertEqual(capture.kind.value, "gateway_site")
        self.assertEqual(capture.rows[0]["normalized_site"], "api.cat.example")
        self.assertEqual(capture.rows[0]["site_name"], "Cat Gateway")
        key, _, state, _ = normalize_raw_observation(capture.rows[0], capture.source, capture.kind, batch_id="b", run_id="r")
        self.assertEqual(key, "gateway_site:api.cat.example")
        self.assertEqual(state, "valid")

    def test_unknown_card_markup_produces_no_untrusted_rows(self) -> None:
        capture = parse_priceai_page(
            get_source("priceai-transit-api"),
            "<article><a href='https://other.example'>untrusted</a></article>",
            observed_at="2026-08-29T14:57:00Z",
        )

        self.assertEqual(capture.rows, [])

