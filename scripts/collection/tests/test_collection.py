#!/usr/bin/env python3
"""Python tests for collection defaults, skip rules, caps, and merge."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_lib.config import (  # noqa: E402
    DEFAULT_ENABLED,
    DEFAULT_INTERVAL_MINUTES,
    DEFAULT_MAX_ITEMS_PER_RUN,
    UNLIMITED_ITEMS,
    apply_item_cap,
    default_source,
    normalize_source,
    source_may_request_network,
    validate_sources,
)
from collection_lib.merge import merge_observations  # noqa: E402
from collection_lib.whitelist import filter_observation  # noqa: E402
from collect import cmd_legacy_recover, cmd_legacy_report, cmd_merge_import, collect_rows, load_sources  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        source = default_source({"id": "x", "target_domain": "example.invalid"})
        self.assertEqual(source["enabled"], DEFAULT_ENABLED)
        self.assertFalse(source["enabled"])
        self.assertEqual(source["interval_minutes"], DEFAULT_INTERVAL_MINUTES)
        self.assertEqual(source["max_items_per_run"], DEFAULT_MAX_ITEMS_PER_RUN)
        self.assertEqual(UNLIMITED_ITEMS, 0)

    def test_zero_means_unlimited_cap(self):
        rows = list(range(5))
        self.assertEqual(apply_item_cap(rows, 0), rows)
        self.assertEqual(apply_item_cap(rows, 2), [0, 1])

    def test_source_cannot_include_or_override_site_score(self):
        with self.assertRaises(ValueError):
            normalize_source({"id": "x", "target_domain": "example.invalid", "score": 99})
        source = default_source({"id": "x", "target_domain": "example.invalid"})
        self.assertNotIn("score", source)
        self.assertNotIn("site_score", source)

    def test_unapproved_source_cannot_request_network(self):
        source = normalize_source({"id": "x", "target_domain": "example.invalid", "approval_status": "draft"})
        self.assertFalse(source_may_request_network(source))
        approved = normalize_source({"id": "x", "target_domain": "example.invalid", "approval_status": "approved"})
        self.assertTrue(source_may_request_network(approved))

    def test_approved_source_requires_exact_allowlisted_public_url(self):
        errors = validate_sources([{"id": "approved", "target_domain": "example.com", "approval_status": "approved", "public_url": "https://example.com/data", "allowlist_urls": ["https://example.com/other"]}])
        self.assertEqual(errors, ["approved: approved source requires public_url in allowlist_urls"])


class MergeTests(unittest.TestCase):
    def test_same_priority_keeps_lowest_price_and_class_rank(self):
        sources = {
            "priceai-channels": {"id": "priceai-channels", "source_class": "aggregator", "priority": 30},
            "openprice-products": {"id": "openprice-products", "source_class": "aggregator", "priority": 10},
            "lingxi-api": {"id": "lingxi-api", "source_class": "site_api", "priority": 40},
            "cardnav-home": {"id": "cardnav-home", "source_class": "aggregator", "priority": 20},
        }
        rows = [
            {"normalized_site": "shop-a", "source_id": "priceai-channels", "price": 10, "currency": "CNY"},
            {"normalized_site": "shop-a", "source_id": "openprice-products", "price": 1, "currency": "CNY", "region": "CN"},
            {"normalized_site": "gw-a", "source_id": "cardnav-home", "price": 3, "model_or_plan": "gpt-4o"},
            {"normalized_site": "gw-a", "source_id": "lingxi-api", "price": 5, "model_or_plan": "gpt-4o"},
            {"normalized_site": "shop-b", "source_id": "priceai-channels", "price": 8},
            {"normalized_site": "shop-b", "source_id": "priceai-channels", "price": 4},
        ]
        merged = {row["normalized_site"]: row for row in merge_observations(rows, sources)}
        self.assertEqual(merged["shop-a"]["price"], 10)
        self.assertEqual(merged["shop-a"]["region"], "CN")
        self.assertEqual(merged["gw-a"]["source_id"], "lingxi-api")
        self.assertEqual(merged["shop-b"]["price"], 4)

    def test_whitelist_strips_html(self):
        cleaned = filter_observation({"normalized_site": "a", "html": "<p>", "cookie": "x", "price": 1})
        self.assertNotIn("html", cleaned)
        self.assertNotIn("cookie", cleaned)
        self.assertEqual(cleaned["price"], 1)


class CliFixtureTests(unittest.TestCase):
    def test_legacy_recovery_requires_confirmation_and_exposes_diagnosis(self):
        class Connection:
            def close(self):
                self.closed = True

        connection = Connection()
        with self.assertRaises(ValueError):
            cmd_legacy_recover("no", "recovery-1")
        with patch("collect.open_local_connection", return_value=connection), patch("collect.apply_migrations"), patch("collect.CollectionRepository", return_value="repository"), patch("collect.LegacyDirectPublishRecovery") as recovery:
            recovery.return_value.diagnose.return_value = {"recoverable": 1, "ambiguous": 2}
            self.assertEqual(cmd_legacy_report(), 0)
            recovery.return_value.recover.return_value = {"recovered": 1}
            self.assertEqual(cmd_legacy_recover("RECOVER_LEGACY", "recovery-1"), 0)
        recovery.return_value.recover.assert_called_once_with("repository", "recovery-1")

    def test_merge_import_command_requires_explicit_batch_and_delegates(self):
        class Connection:
            def close(self):
                self.closed = True

        connection = Connection()
        with patch("collect.open_local_connection", return_value=connection), patch("collect.apply_migrations") as migrate, patch("collect.CollectionRepository", return_value="repository"), patch("collect.RuntimeImporter") as importer:
            importer.return_value.merge_import_batch.return_value = {"batch_id": "batch-1", "runtime_writes": 1}
            self.assertEqual(cmd_merge_import("batch-1"), 0)
        migrate.assert_called_once_with(connection)
        importer.return_value.merge_import_batch.assert_called_once_with("repository", "batch-1")

    def test_approved_source_uses_allowlisted_fetch_instead_of_fixture(self):
        source = {
            "id": "approved", "name": "Approved", "source_class": "site_api", "target_domain": "example.com",
            "priority": 1, "enabled": False, "interval_minutes": 60, "max_items_per_run": 1000,
            "approval_status": "approved", "public_url": "https://example.com/data", "allowlist_urls": ["https://example.com/data"],
        }
        response_rows = [{"normalized_site": "example.com", "model_or_plan": "gpt-plus", "price": 1}]
        with patch("collect.fetch_approved_json", return_value=("[]", response_rows, "application/json")) as fetch:
            rows, stats = collect_rows([source], ignore_enabled=True)
        fetch.assert_called_once_with(source)
        self.assertEqual(stats["network_requests"], 1)
        self.assertEqual(rows[0]["normalized_site"], "example.com")

    def test_unapproved_sources_use_fixtures_without_network(self):
        sources = load_sources(ROOT / "sources.example.json")
        rows, stats = collect_rows(sources, ignore_enabled=True)
        self.assertEqual(stats["network_requests"], 0)
        self.assertGreater(stats["skipped_unapproved"], 0)
        self.assertGreater(stats["raw"], 0)
        self.assertTrue(all("html" not in row for row in rows))

    def test_example_sources_validate_and_lack_score(self):
        sources = load_sources(ROOT / "sources.example.json")
        self.assertEqual(validate_sources(sources), [])
        self.assertTrue(all("score" not in source for source in sources))
        self.assertTrue(all(source["enabled"] is False for source in sources))
        self.assertTrue(all(source["max_items_per_run"] in (0, 1000) for source in sources))


class GuiSmokeTests(unittest.TestCase):
    def test_gui_entry_launches_console_shell(self):
        script = "\n".join((
            "import sys, tkinter as tk",
            f"sys.path.insert(0, {str(ROOT)!r})",
            "from console_app import ConsoleApp",
            "root = tk.Tk(); root.withdraw()",
            "app = ConsoleApp(root)",
            "assert 'collect.shops' in app.pages",
            "assert 'operations' in app.pages",
            "root.destroy()",
        ))
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
