from __future__ import annotations

import unittest

from scripts.crawlee_collection.sources import (
    GATEWAY_REFERENCE_SOURCE_IDS,
    MAX_CONCURRENCY,
    PRICEAI_SOURCE_IDS,
    get_source,
    list_sources,
    require_allowed_source,
)


class SourceRegistryTests(unittest.TestCase):
    def test_registry_contains_only_approved_fixed_source_pages(self) -> None:
        sources = list_sources()

        self.assertEqual(MAX_CONCURRENCY, 1)
        self.assertEqual(
            [source.source_id for source in sources],
            [*PRICEAI_SOURCE_IDS, *GATEWAY_REFERENCE_SOURCE_IDS],
        )
        self.assertEqual(
            [source.url for source in sources],
            [
                "https://priceai.cc/channels",
                "https://priceai.cc/official-api",
                "https://priceai.cc/api-transit",
                "https://priceai.cc/api-transit/models",
                "https://cardnav.xyz/llm-gateway",
                "https://raw.githubusercontent.com/hvoyai/awesome-ai-api/main/data.json",
            ],
        )
        self.assertEqual(
            [source.record_kind.value for source in sources],
            [
                "shop_product",
                "official_plan",
                "gateway_site",
                "gateway_site",
                "gateway_site",
                "gateway_site",
            ],
        )

    def test_registry_returns_immutable_source_by_identifier(self) -> None:
        source = get_source("priceai-transit-api")

        self.assertEqual(source.page_type, "transit_api")
        self.assertFalse(source.enabled)
        self.assertEqual(source.source_class, "aggregator")

    def test_unregistered_source_and_url_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown source"):
            get_source("anything-else")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            require_allowed_source("priceai-card-subscriptions", "https://priceai.cc/other")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            require_allowed_source("priceai-card-subscriptions", "https://merchant.example/item")

    def test_cardnav_gateway_source_has_a_fixed_list_entry(self) -> None:
        source = get_source("cardnav-gateway-details")

        self.assertEqual(source.url, "https://cardnav.xyz/llm-gateway")
        self.assertEqual(source.record_kind.value, "gateway_site")

    def test_hvoyai_reference_source_is_exact_and_not_a_price_or_model_source(self) -> None:
        self.assertEqual(GATEWAY_REFERENCE_SOURCE_IDS, ("hvoyai-awesome-ai-api",))

        source = get_source("hvoyai-awesome-ai-api")

        self.assertEqual(
            source.url,
            "https://raw.githubusercontent.com/hvoyai/awesome-ai-api/main/data.json",
        )
        self.assertEqual(source.page_type, "hvoyai_transit_reference_json")
        self.assertEqual(source.record_kind.value, "gateway_site")
        self.assertEqual(source.source_class, "reference")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            require_allowed_source(
                "hvoyai-awesome-ai-api",
                "https://github.com/hvoyai/awesome-ai-api/blob/main/README.md",
            )
