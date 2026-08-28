#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.contracts import RecordKind  # noqa: E402
from collection_lib.public_data import list_public_rows  # noqa: E402
from console_tabs.collection_tab import KIND_BY_PAGE  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
