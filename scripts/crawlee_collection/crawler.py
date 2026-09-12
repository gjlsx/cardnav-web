"""PlaywrightCrawler adapter that visits one allowlisted URL and never follows links."""
from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from typing import Any

from .gateway import build_cardnav_captures, discover_gateway_listings, is_allowed_cardnav_detail_url
from .sources import MAX_CONCURRENCY, BrowserSource, require_allowed_source

LIST_LOAD_MORE_SELECTOR = '[data-gateway-load-more="sites"]'
LIST_ROW_SELECTOR = "table tbody tr"
DETAIL_LOAD_MORE_SELECTOR = '[data-gateway-detail-load-more="prices"]'
DETAIL_ROW_SELECTOR = "table tbody tr"
EXPAND_WAIT_MS = 15_000


async def expand_paginated_table(
    page: Any,
    button_selector: str,
    row_selector: str,
    *,
    max_rows: int,
    max_rounds: int = 200,
    wait_ms: int = EXPAND_WAIT_MS,
) -> int:
    """Click load-more until the full rendered table is present.

    Stops only when the button is gone/hidden, max_rows is reached, or a click
    produces no new rows after waiting for the deferred fetch.
    """
    target = max_rows if max_rows > 0 else 10_000
    rows = page.locator(row_selector)
    count = await rows.count()
    for _ in range(max(1, max_rounds)):
        if count >= target:
            return count
        button = page.locator(button_selector)
        if await button.count() == 0 or not await button.first.is_visible():
            return count
        before = count
        await button.first.click()
        try:
            await page.wait_for_function(
                "([selector, previous]) => document.querySelectorAll(selector).length > previous",
                arg=[row_selector, before],
                timeout=wait_ms,
            )
        except Exception:
            count = await rows.count()
            if count <= before:
                return count
        count = await rows.count()
    return count


class PlaywrightPageFetcher:
    """Fetch a single approved page through Crawlee Playwright with concurrency 1."""

    max_concurrency = MAX_CONCURRENCY

    def __init__(self, runner: Callable[[BrowserSource], str] | None = None) -> None:
        if MAX_CONCURRENCY != 1:
            raise ValueError("browser max_concurrency must stay 1")
        self._runner = runner

    def fetch_html(self, source: BrowserSource) -> str:
        require_allowed_source(source.source_id, source.url)
        if self._runner is not None:
            return self._runner(source)
        return asyncio.run(self._playwright_fetch(source))

    def fetch_cardnav_captures(
        self,
        model_source: BrowserSource,
        list_source: BrowserSource,
        observed_at: str,
        max_items_per_run: int,
    ):
        """Collect the approved model catalog, CardNav list, and one-level detail pages serially."""
        model_html = self.fetch_html(model_source)
        if self._runner is not None:
            list_html = self._runner(list_source)
            listings = discover_gateway_listings(list_html)
            if max_items_per_run > 0:
                listings = listings[:max_items_per_run]
            detail_pages = {listing.detail_url: self._runner(type(list_source)(**{**list_source.__dict__, "url": listing.detail_url})) for listing in listings}
        else:
            list_html, detail_pages = asyncio.run(self._collect_cardnav_pages(list_source, max_items_per_run))
        return build_cardnav_captures(model_source, model_html, list_source, list_html, detail_pages, observed_at=observed_at)

    async def _playwright_fetch(self, source: BrowserSource) -> str:
        from crawlee import ConcurrencySettings
        from crawlee.configuration import Configuration
        from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

        html = {"value": ""}
        crawler = PlaywrightCrawler(
            max_requests_per_crawl=1,
            max_crawl_depth=0,
            retry_on_blocked=False,
            concurrency_settings=ConcurrencySettings(min_concurrency=1, max_concurrency=1, desired_concurrency=1),
            configuration=Configuration(storage_dir=tempfile.mkdtemp(prefix="crawlee-priceai-")),
            headless=True,
        )

        @crawler.router.default_handler
        async def handler(context: PlaywrightCrawlingContext) -> None:
            current = str(context.request.url).split("?", 1)[0].rstrip("/")
            allowed = source.url.rstrip("/")
            if current != allowed:
                raise ValueError(f"URL is not allowed for {source.source_id}: {context.request.url}")
            html["value"] = (
                await context.page.locator("body").inner_text()
                if source.page_type == "hvoyai_transit_reference_json"
                else await context.page.content()
            )

        await crawler.run([source.url])
        return html["value"]

    async def _collect_cardnav_pages(self, source: BrowserSource, max_items_per_run: int) -> tuple[str, dict[str, str]]:
        """Use Crawlee Playwright for the list and only its directly rendered detail links."""
        from crawlee import ConcurrencySettings
        from crawlee.configuration import Configuration
        from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

        list_html = {"value": ""}
        list_crawler = PlaywrightCrawler(
            max_requests_per_crawl=1,
            max_crawl_depth=0,
            retry_on_blocked=False,
            concurrency_settings=ConcurrencySettings(min_concurrency=1, max_concurrency=1, desired_concurrency=1),
            configuration=Configuration(storage_dir=tempfile.mkdtemp(prefix="crawlee-cardnav-list-")),
            headless=True,
        )

        @list_crawler.router.default_handler
        async def list_handler(context: PlaywrightCrawlingContext) -> None:
            if str(context.request.url).split("?", 1)[0].rstrip("/") != source.url.rstrip("/"):
                raise ValueError(f"URL is not allowed for {source.source_id}: {context.request.url}")
            await expand_paginated_table(
                context.page,
                LIST_LOAD_MORE_SELECTOR,
                LIST_ROW_SELECTOR,
                max_rows=max_items_per_run,
            )
            list_html["value"] = await context.page.content()

        await list_crawler.run([source.url])
        listings = discover_gateway_listings(list_html["value"])
        if max_items_per_run > 0:
            listings = listings[:max_items_per_run]
        detail_pages: dict[str, str] = {}
        if not listings:
            return list_html["value"], detail_pages
        detail_crawler = PlaywrightCrawler(
            max_requests_per_crawl=len(listings),
            max_crawl_depth=0,
            retry_on_blocked=False,
            concurrency_settings=ConcurrencySettings(min_concurrency=1, max_concurrency=1, desired_concurrency=1),
            configuration=Configuration(storage_dir=tempfile.mkdtemp(prefix="crawlee-cardnav-detail-")),
            headless=True,
        )

        @detail_crawler.router.default_handler
        async def detail_handler(context: PlaywrightCrawlingContext) -> None:
            current = str(context.request.url).split("?", 1)[0].rstrip("/")
            if not is_allowed_cardnav_detail_url(current):
                raise ValueError(f"CardNav detail URL is not allowed: {context.request.url}")
            await expand_paginated_table(
                context.page,
                DETAIL_LOAD_MORE_SELECTOR,
                DETAIL_ROW_SELECTOR,
                max_rows=max_items_per_run,
            )
            detail_pages[current] = await context.page.content()

        await detail_crawler.run([listing.detail_url for listing in listings])
        return list_html["value"], detail_pages
