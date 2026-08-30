from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.crawlee_collection.catch_config import load_catch_config, source_interval_seconds
from scripts.crawlee_collection.gui_commands import button_label, cli_argv


class HvoyaiScheduleTests(unittest.TestCase):
    def test_example_keeps_hvoyai_disabled_with_an_editable_eight_hour_interval(self) -> None:
        config = load_catch_config(Path("scripts/crawlee_collection/catch.config.example"))

        setting = config["collect"]["source_settings"]["hvoyai-awesome-ai-api"]
        self.assertFalse(setting["enabled"])
        self.assertEqual(setting["interval_minutes"], 480)
        self.assertEqual(source_interval_seconds(config, "hvoyai-awesome-ai-api"), 28_800)

    def test_invalid_hvoyai_interval_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catch.config"
            path.write_text(json.dumps({
                "collect": {"source_settings": {"hvoyai-awesome-ai-api": {"enabled": False, "interval_minutes": 0}}},
                "merge": {},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "interval_minutes"):
                load_catch_config(path)

    def test_gui_uses_fixed_cli_for_hvoyai_once_loop_and_stop(self) -> None:
        source_id = "hvoyai-awesome-ai-api"
        self.assertEqual(cli_argv("collect-once", source_id)[-3:], ["collect", "--source", source_id])
        self.assertEqual(cli_argv("collect", source_id)[-4:], ["collect", "--source", source_id, "--loop"])
        self.assertEqual(cli_argv("collect-stop", source_id), ["stop", "collect", source_id])
        self.assertEqual(button_label("collect-once", source_id), "抓取一次参考")


if __name__ == "__main__":
    unittest.main()
