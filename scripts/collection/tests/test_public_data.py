#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib import public_data  # noqa: E402
from collection_lib.public_data import list_public_rows  # noqa: E402
from console_tabs.collection_tab import KIND_BY_PAGE  # noqa: E402
from console_tabs.site_config_tab import parse_editor_payload  # noqa: E402


class PublicDataTests(unittest.TestCase):
    def test_collect_pages_map_to_four_record_kinds(self):
        self.assertEqual(KIND_BY_PAGE["collect.shops"], RecordKind.SHOP_PRODUCT)
        self.assertEqual(KIND_BY_PAGE["collect.gateway"], RecordKind.GATEWAY_SITE)
        self.assertEqual(set(KIND_BY_PAGE), {"collect.gateway", "collect.shops", "collect.official", "collect.leaderboard"})

    def test_list_public_rows_uses_repository_query(self):
        class Repo:
            def query(self, sql, params=()):
                return [{"site_id": "collected-a.example", "standard_product": "chatgpt-plus", "name": "x", "price": "1", "price_number": 1, "currency_code": "CNY", "in_stock": 1}]

        rows = list_public_rows(Repo(), RecordKind.SHOP_PRODUCT)
        self.assertEqual(rows[0]["record_key"], "shop_product:a.example:chatgpt-plus")

    def test_gateway_rows_include_editable_region_and_benefit_fields(self):
        class Repo:
            def query(self, sql, params=()):
                self.sql = sql
                return [{"site_id": "collected-a", "slug": "a", "name": "A", "host": "a.example", "score": 50, "region": "中国", "benefit_text": "福利说明"}]

        repository = Repo()
        rows = list_public_rows(repository, RecordKind.GATEWAY_SITE)
        self.assertIn("region", repository.sql)
        self.assertIn("benefit_text", repository.sql)
        self.assertEqual(rows[0]["region"], "中国")
        self.assertEqual(rows[0]["benefit_text"], "福利说明")

    def test_site_config_editor_keeps_known_fields_editable(self):
        payload = parse_editor_payload(
            {"site_id": "collected-a", "region": "", "benefit_text": "", "score": 50},
            "region=中国大陆\nbenefit_text=注册送体验金\nunknown=ignored",
        )
        self.assertEqual(payload["region"], "中国大陆")
        self.assertEqual(payload["benefit_text"], "注册送体验金")
        self.assertNotIn("unknown", payload)

    def test_homepage_announcement_is_saved_to_the_existing_public_snapshot(self):
        self.assertTrue(hasattr(public_data, "save_homepage_announcement"))
        self.assertTrue(hasattr(public_data, "load_homepage_announcement"))


if __name__ == "__main__":
    unittest.main()
