from __future__ import annotations

import json
import unittest

from scripts.collection.collection_lib.contracts import RecordKind
from scripts.collection.collection_lib.pipeline import SourceCapture
from io import StringIO
from unittest.mock import patch

from scripts.crawlee_collection.catch_config import configured_sources
from scripts.crawlee_collection.sources import MAX_CONCURRENCY, get_source, list_sources
from scripts.crawlee_collection.worker import MergeImportWorker


SHOP_HTML = """
<article data-collection-card="shop">
  <a href="https://cc-cat.example/products/gemini-pro"><span>cc-cat</span></a>
  <h3>Gemini Pro 月卡</h3><span>¥29.90</span><span>有货</span>
</article>
"""

HVOYAI_JSON = '{"updatedDate":"2026-08-30","sites":[{"rank":1,"name":"Reference API","url":"https://www.hvoyai.com/sites/reference-api/","modelCount":1,"models":["OpenAI"]}]}'


class _Fetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.max_concurrency = MAX_CONCURRENCY

    def fetch_html(self, source) -> str:
        from scripts.crawlee_collection.sources import require_allowed_source

        require_allowed_source(source.source_id, source.url)
        self.urls.append(source.url)
        if source.page_type == "card_subscriptions":
            return SHOP_HTML
        if source.page_type == "hvoyai_transit_reference_json":
            return HVOYAI_JSON
        return "<html></html>"

    def fetch_cardnav_captures(self, model_source, list_source, observed_at: str, max_items_per_run: int):
        self.urls.extend([model_source.url, list_source.url])
        return [
            SourceCapture(
                source={"id": list_source.source_id, "public_url": list_source.url},
                body="<html></html>",
                rows=[{"normalized_site": "linkai.shop", "site_name": "LinkAi", "observed_at": observed_at}],
                content_type="text/html",
                kind=RecordKind.GATEWAY_SITE,
            )
        ]


class _Store:
    def __init__(self) -> None:
        self.persisted: list[object] = []
        self.merged: list[str] = []
        self.closed = 0

    def persist_captures(self, captures, trigger: str = "manual"):
        self.persisted.append((trigger, [capture.source["id"] for capture in captures]))
        return {"batch_id": "batch-1", "stats": {"raw_records": len(captures)}, "error": None}

    def list_raw_batches(self):
        return [{"batch_id": "batch-1", "status": "raw_completed", "raw_count": 1}]

    def ready_batch_ids(self) -> list[str]:
        return ["batch-1"]

    def merge_batch(self, batch_id: str):
        self.merged.append(batch_id)
        return {"batch_id": batch_id, "runtime_writes": 1}

    def close_if_idle(self) -> bool:
        self.closed += 1
        return False


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        MergeImportWorker.reset()
        self.fetcher = _Fetcher()
        self.store = _Store()
        self.services = {"fetcher": self.fetcher, "store": self.store}

    def tearDown(self) -> None:
        MergeImportWorker.reset()

    def _run(self, argv: list[str]) -> tuple[int, dict]:
        from scripts.crawlee_collection.cli import main

        stdout = StringIO()
        with patch("sys.stdout", stdout):
            code = main(argv, services=self.services)
        payload = json.loads(stdout.getvalue() or "{}")
        return code, payload

    def test_check_config_lists_only_allowlisted_sources_and_concurrency(self) -> None:
        code, payload = self._run(["check-config"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["max_concurrency"], 1)
        self.assertEqual([item["source_id"] for item in payload["sources"]], [source.source_id for source in list_sources()])
        self.assertEqual(payload["errors"], [])

    def test_collect_all_uses_playwright_fetcher_and_persists_one_raw_batch(self) -> None:
        code, payload = self._run(["collect", "--all"])
        configured = configured_sources()
        self.assertEqual(code, 0)
        self.assertEqual(self.fetcher.urls, [
            *[source.url for source in configured if source.page_type not in {"cardnav_gateway_details", "hvoyai_transit_reference_json"}],
            "https://priceai.cc/api-transit/models",
            "https://cardnav.xyz/llm-gateway",
            *[source.url for source in configured if source.page_type == "hvoyai_transit_reference_json"],
        ])
        self.assertEqual(self.store.persisted, [("manual", [source.source_id for source in configured])])
        self.assertEqual(payload["batch_id"], "batch-1")
        self.assertEqual(self.fetcher.max_concurrency, 1)

    def test_collect_rejects_unknown_source_and_has_no_url_flag(self) -> None:
        from scripts.crawlee_collection.cli import build_parser

        with self.assertRaises(SystemExit):
            build_parser().parse_args(["collect", "--url", "https://merchant.example/item"])
        code, payload = self._run(["collect", "--source", "not-a-source"])
        self.assertEqual(code, 2)
        self.assertIn("unknown source", payload["error"])
        self.assertEqual(self.store.persisted, [])

    def test_collect_cardnav_gateway_runs_its_priceai_catalog_dependency(self) -> None:
        code, payload = self._run(["collect", "--source", "cardnav-gateway-details"])

        self.assertEqual(code, 0)
        self.assertEqual(self.fetcher.urls, ["https://priceai.cc/api-transit/models", "https://cardnav.xyz/llm-gateway"])
        self.assertEqual(self.store.persisted, [("manual", ["cardnav-gateway-details"])])
        self.assertEqual(payload["batch_id"], "batch-1")

    def test_merge_once_and_worker_once_are_explicit_and_serial(self) -> None:
        collect_code, _ = self._run(["collect", "--source", "priceai-card-subscriptions"])
        merge_code, merge_payload = self._run(["merge-once", "--batch", "batch-1"])
        worker_code, worker_payload = self._run(["worker", "--once"])
        self.assertEqual((collect_code, merge_code, worker_code), (0, 0, 0))
        self.assertEqual(self.store.merged, ["batch-1", "batch-1"])
        self.assertEqual(merge_payload["runtime_writes"], 1)
        self.assertEqual(worker_payload["results"][0]["batch_id"], "batch-1")
        self.assertIsNone(MergeImportWorker._running)

    def test_playwright_fetcher_rejects_non_allowlisted_url(self) -> None:
        from scripts.crawlee_collection.crawler import PlaywrightPageFetcher

        fetcher = PlaywrightPageFetcher(runner=lambda source: "<html></html>")
        self.assertEqual(fetcher.max_concurrency, 1)
        source = get_source("priceai-card-subscriptions")
        broken = type(source)(**{**source.__dict__, "url": "https://merchant.example/item"})
        with self.assertRaisesRegex(ValueError, "not allowed"):
            fetcher.fetch_html(broken)
