#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from console_lib.operations import preview, run_confirmed  # noqa: E402
from console_lib.scheduler import LocalScheduler  # noqa: E402


class OperationsTests(unittest.TestCase):
    def test_wrong_confirmation_does_not_run(self):
        with self.assertRaises(ValueError):
            run_confirmed("backup", "nope")
        self.assertIn("howtorunvpsnew.md", preview("publish"))
        self.assertIn("export-mysql", preview("backup"))


class SchedulerTests(unittest.TestCase):
    def test_disabled_sources_are_not_due(self):
        scheduler = LocalScheduler(lambda *_a: None, lambda source: None)
        due = scheduler.due_sources([{"id": "a", "enabled": False, "interval_minutes": 1}, {"id": "b", "enabled": True, "interval_minutes": 60}])
        self.assertEqual([item["id"] for item in due], ["b"])
        scheduler.mark_ran({"id": "b", "interval_minutes": 60})
        later = scheduler.due_sources([{"id": "b", "enabled": True, "interval_minutes": 60}])
        self.assertEqual(later, [])


if __name__ == "__main__":
    unittest.main()
