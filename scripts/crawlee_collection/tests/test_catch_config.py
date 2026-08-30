from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.crawlee_collection.catch_config import configured_sources, load_catch_config
from scripts.crawlee_collection.gui_commands import MODULE_TABS, button_label, cli_argv


class CatchConfigTests(unittest.TestCase):
    def test_example_config_only_allows_registered_collection_sources(self) -> None:
        config = load_catch_config(Path("scripts/crawlee_collection/catch.config.example"))

        self.assertFalse(config["collect"]["enabled"])
        self.assertEqual(
            config["collect"]["source_ids"],
            ["priceai-card-subscriptions", "priceai-official-api", "priceai-transit-api", "cardnav-gateway-details", "hvoyai-awesome-ai-api"],
        )
        self.assertEqual(config["collect"]["interval_seconds"], 3600)
        self.assertFalse(config["collect"]["source_settings"]["hvoyai-awesome-ai-api"]["enabled"])
        self.assertEqual(config["collect"]["source_settings"]["hvoyai-awesome-ai-api"]["interval_minutes"], 480)
        self.assertFalse(config["merge"]["enabled"])
        self.assertEqual(config["merge"]["poll_interval_seconds"], 10)
        self.assertEqual(
            [source.source_id for source in configured_sources(Path("scripts/crawlee_collection/catch.config.example"))],
            config["collect"]["source_ids"],
        )

    def test_unknown_source_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catch.config"
            path.write_text(json.dumps({"collect": {"source_ids": ["merchant-x"]}, "merge": {}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not allowed"):
                load_catch_config(path)


class GuiCommandTests(unittest.TestCase):
    def test_gui_has_collect_tab_and_merge_tab(self) -> None:
        self.assertEqual([item[1] for item in MODULE_TABS], ["采集", "入库"])
        self.assertEqual(MODULE_TABS[0][2], ("collect-once", "collect", "collect-stop"))
        self.assertEqual(MODULE_TABS[1][2], ("merge", "merge-stop"))

    def test_tab_buttons_map_to_fixed_cli_commands(self) -> None:
        source = "priceai-card-subscriptions"
        self.assertEqual(cli_argv("collect", source)[-4:], ["collect", "--source", source, "--loop"])
        self.assertEqual(cli_argv("merge", source)[-4:], ["worker", "--source", source, "--loop"])
        self.assertEqual(cli_argv("collect-stop", source), ["stop", "collect", source])
        self.assertEqual(cli_argv("merge-stop", source), ["stop", "merge", source])
        self.assertEqual(button_label("collect-stop", source), "停止卡网")
        self.assertEqual(button_label("merge-stop", "priceai-official-api"), "停止官方")
        self.assertEqual(button_label("merge-stop", "priceai-transit-api"), "停止中转")
        self.assertEqual(button_label("merge-stop", "cardnav-gateway-details"), "停止中转")
        self.assertEqual(button_label("collect", source), "采集卡网")
        self.assertEqual(button_label("merge", source), "入库卡网")

    def test_gui_builds_collect_and_merge_tabs(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        from scripts.crawlee_collection.gui import CliJobs, ModuleTab

        root = tk.Tk()
        root.withdraw()
        try:
            notebook = ttk.Notebook(root)
            jobs = CliJobs()
            titles = []
            for module_key, title, actions in MODULE_TABS:
                tab = ModuleTab(notebook, module_key, actions, jobs)
                notebook.add(tab, text=title)
                titles.append(str(notebook.tab(tab, "text")))
            self.assertEqual(titles, ["采集", "入库"])
        finally:
            root.destroy()
