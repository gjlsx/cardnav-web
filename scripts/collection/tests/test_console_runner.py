#!/usr/bin/env python3
"""Console runner and per-page log isolation tests."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from console_lib.page_log import PageLogs  # noqa: E402
from console_lib.task_runner import TaskRunner  # noqa: E402


class FakeAfter:
    def __init__(self):
        self.pending = []

    def __call__(self, _ms, fn):
        self.pending.append(fn)

    def drain(self):
        while self.pending:
            fn = self.pending.pop(0)
            fn()


class RunnerTests(unittest.TestCase):
    def test_same_action_does_not_run_concurrently_and_events_are_queued(self):
        after = FakeAfter()
        runner = TaskRunner(after)
        events = []
        started = time.time()
        runner.submit("collect.shops:run", lambda: time.sleep(0.05) or "ok", lambda *item: events.append(item))
        busy = runner.submit("collect.shops:run", lambda: "nope", lambda *item: events.append(item))
        deadline = time.time() + 2
        while time.time() < deadline:
            after.drain()
            if "ok" in [item[0] for item in events] and "done" in [item[0] for item in events]:
                break
            time.sleep(0.01)
        kinds = [item[0] for item in events]
        self.assertIn("start", kinds)
        self.assertIn("busy", kinds)
        self.assertFalse(busy)
        self.assertIn("ok", kinds)
        self.assertIn("done", kinds)
        self.assertGreaterEqual(time.time() - started, 0.04)

    def test_page_logs_do_not_mix(self):
        logs = PageLogs()
        logs.append("collect.shops", "shop-only")
        logs.append("operations", "ops-only")
        self.assertIn("shop-only", logs.text("collect.shops"))
        self.assertNotIn("ops-only", logs.text("collect.shops"))
        self.assertIn("ops-only", logs.text("operations"))
        self.assertNotIn("shop-only", logs.text("operations"))


class ShellSmokeTests(unittest.TestCase):
    def test_console_shows_three_root_tabs_and_four_collect_tabs(self):
        import tkinter as tk
        from console_app import COLLECT_PAGES, ConsoleApp

        root = tk.Tk()
        root.withdraw()
        app = ConsoleApp(root)
        notebook = root.winfo_children()[0]
        texts = [notebook.tab(i, "text") for i in notebook.tabs()]
        self.assertEqual(texts, ["采集数据", "网站配置", "合作运维"])
        self.assertEqual([key for key, _title in COLLECT_PAGES], ["collect.gateway", "collect.shops", "collect.official", "collect.leaderboard"])
        self.assertEqual(len(app.pages), 6)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
