#!/usr/bin/env python3
"""Console runner and per-page log isolation tests."""
from __future__ import annotations

import sys
import subprocess
import textwrap
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from console_lib.page_log import PageLogs  # noqa: E402
from console_lib.source_control import SourceRunControl  # noqa: E402
from console_lib.source_test import run_source_test  # noqa: E402
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
    def test_source_stop_flag_stops_loop_and_reports_message(self):
        control = SourceRunControl()
        stop = control.start_loop("xxa")
        self.assertFalse(stop.is_set())
        self.assertTrue(control.begin("xxa") is stop)
        self.assertEqual(control.stop("xxa"), "task xxa is stop!")
        self.assertTrue(stop.is_set())
        self.assertFalse(control.is_looping("xxa"))
        self.assertTrue(control.should_stop("xxa"))

    def test_source_test_runs_only_fixed_project_test_py_and_captures_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "source_tests" / "test.py"
            script.parent.mkdir()
            script.write_text("import sys\nprint('input=' + sys.argv[2])\nprint('error-line', file=sys.stderr)\n", encoding="utf-8")
            result = run_source_test(root, "xxa")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("input=xxa", result["stdout"])
        self.assertIn("error-line", result["stderr"])
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
    def _console_probe(self, assertions: str) -> None:
        script = "\n".join((
            "import sys, tkinter as tk",
            f"sys.path.insert(0, {str(ROOT)!r})",
            "from console_app import ConsoleApp, COLLECT_PAGES",
            "root = tk.Tk(); root.withdraw()",
            "app = ConsoleApp(root)",
            textwrap.dedent(assertions).strip(),
            "root.destroy()",
        ))
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_console_shows_three_root_tabs_and_four_collect_tabs(self):
        self._console_probe("""
        notebook = root.winfo_children()[0]
        texts = [notebook.tab(i, "text") for i in notebook.tabs()]
        assert texts == ["采集数据", "网站配置", "合作运维"], texts
        assert [key for key, _title in COLLECT_PAGES] == ["collect.gateway", "collect.shops", "collect.official", "collect.leaderboard"]
        assert len(app.pages) == 6
        """)

    def test_collection_workspace_supports_batch_capture_and_explicit_runtime_import(self):
        self._console_probe("""
        workspace = next(item for item in app.workspaces if item.page.page_key == "collect.shops")
        assert str(workspace.source_list.cget("selectmode")) == "extended"
        assert workspace.capture_button.cget("text") == "抓取选中来源（同一批次）"
        assert workspace.import_button.cget("text") == "合并并入库运行数据表"
        assert str(workspace.open_url_button.cget("state")) == "disabled"
        assert "统一 raw 审计记录" in workspace.view_names
        assert "当前运行时记录" in workspace.view_names
        """)


if __name__ == "__main__":
    unittest.main()
