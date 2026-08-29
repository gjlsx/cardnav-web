"""PlaywrightCrawler adapter that visits one allowlisted URL and never follows links."""
from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable

from .sources import MAX_CONCURRENCY, BrowserSource, require_allowed_source


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
            html["value"] = await context.page.content()

        await crawler.run([source.url])
        return html["value"]
