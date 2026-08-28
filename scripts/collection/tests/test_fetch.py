from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.fetch import fetch_approved_json  # noqa: E402


class FetchTests(unittest.TestCase):
    def test_approved_source_fetches_only_allowlisted_url(self):
        source = {"approval_status": "approved", "target_domain": "127.0.0.1", "allowlist_urls": ["http://127.0.0.1:8123/data"], "public_url": "http://127.0.0.1:8123/data"}
        with patch("collection_lib.fetch.urlopen") as open_url:
            response = open_url.return_value.__enter__.return_value
            response.read.return_value = b'[{"normalized_site":"shop.example.com"}]'
            response.headers.get_content_type.return_value = "application/json"
            body, rows, content_type = fetch_approved_json(source)
        self.assertEqual(rows[0]["normalized_site"], "shop.example.com")
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, '[{"normalized_site":"shop.example.com"}]')

    def test_rejects_unapproved_or_non_allowlisted_url(self):
        with self.assertRaises(ValueError):
            fetch_approved_json({"approval_status": "draft", "public_url": "http://127.0.0.1/data", "allowlist_urls": ["http://127.0.0.1/data"]})
        with self.assertRaises(ValueError):
            fetch_approved_json({"approval_status": "approved", "public_url": "http://127.0.0.1/no", "allowlist_urls": ["http://127.0.0.1/yes"]})
