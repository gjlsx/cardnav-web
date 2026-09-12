from __future__ import annotations

import unittest

from scripts.crawlee_collection.crawler import expand_paginated_table


class _FakeLocator:
    def __init__(self, page: "_FakePage", selector: str) -> None:
        self._page = page
        self._selector = selector
        self.first = self

    async def count(self) -> int:
        if self._selector == self._page.button_selector:
            return 0 if self._page.button_hidden else 1
        return self._page.rows

    async def is_visible(self) -> bool:
        return self._selector == self._page.button_selector and not self._page.button_hidden

    async def click(self) -> None:
        self._page.pending += self._page.page_size


class _FakePage:
    def __init__(self, *, rows: int, page_size: int, total: int, button_selector: str, row_selector: str) -> None:
        self.rows = rows
        self.page_size = page_size
        self.total = total
        self.button_selector = button_selector
        self.row_selector = row_selector
        self.pending = 0
        self.button_hidden = rows >= total
        self.wait_calls = 0

    def locator(self, selector: str) -> _FakeLocator:
        return _FakeLocator(self, selector)

    async def wait_for_function(self, _expr: str, *, arg: list[object], timeout: int) -> None:
        self.wait_calls += 1
        previous = int(arg[1])
        if self.pending:
            self.rows = min(self.total, self.rows + self.pending)
            self.pending = 0
            self.button_hidden = self.rows >= self.total
        if self.rows <= previous:
            raise TimeoutError("no new rows")


class ExpandPaginatedTableTests(unittest.TestCase):
    def test_keeps_clicking_after_deferred_rows_arrive(self) -> None:
        page = _FakePage(
            rows=20,
            page_size=20,
            total=86,
            button_selector='[data-gateway-load-more="sites"]',
            row_selector="table tbody tr",
        )

        count = self._run(page, max_rows=1000)

        self.assertEqual(count, 86)
        self.assertGreaterEqual(page.wait_calls, 4)
        self.assertTrue(page.button_hidden)

    def test_stops_at_configured_item_cap(self) -> None:
        page = _FakePage(
            rows=20,
            page_size=20,
            total=400,
            button_selector='[data-gateway-load-more="sites"]',
            row_selector="table tbody tr",
        )

        count = self._run(page, max_rows=60)

        self.assertEqual(count, 60)
        self.assertFalse(page.button_hidden)

    def test_does_not_stop_on_the_first_empty_200ms_poll(self) -> None:
        page = _FakePage(
            rows=20,
            page_size=20,
            total=40,
            button_selector='[data-gateway-detail-load-more="prices"]',
            row_selector="table tbody tr",
        )

        count = self._run(page, max_rows=1000)

        self.assertEqual(count, 40)
        self.assertEqual(page.wait_calls, 1)

    def _run(self, page: _FakePage, max_rows: int) -> int:
        return asyncio_run(
            expand_paginated_table(
                page,
                page.button_selector,
                page.row_selector,
                max_rows=max_rows,
                wait_ms=50,
            )
        )


def asyncio_run(coro):  # noqa: ANN001, ANN201
    import asyncio

    return asyncio.run(coro)
