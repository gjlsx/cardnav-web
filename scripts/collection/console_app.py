#!/usr/bin/env python3
"""AI LoveMoney desktop console: collection, site config, operations."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pathlib import Path

from console_lib.page_log import PageLogs
from console_lib.scheduler import LocalScheduler
from console_lib.task_runner import TaskRunner
from console_lib.widgets import WorkPage
from console_tabs.collection_tab import KIND_BY_PAGE, CollectionWorkspace
from console_tabs.operations_tab import OperationsWorkspace
from console_tabs.site_config_tab import SiteConfigWorkspace

COLLECT_PAGES = (
    ("collect.gateway", "中转网站"),
    ("collect.shops", "卡网商品"),
    ("collect.official", "官方网站"),
    ("collect.leaderboard", "模型排行"),
)


class ConsoleApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI LoveMoney 本机网站总控台")
        self.root.minsize(1100, 720)
        self.logs = PageLogs()
        self.runner = TaskRunner(self.root.after)
        self.scheduler = LocalScheduler(self.root.after, lambda source: None)
        self.pages: dict[str, WorkPage] = {}
        self.workspaces = []
        self.db_error = None
        self.repository = None
        self.sources_path = Path(__file__).resolve().parent / "sources.example.json"
        self._try_db()
        self._build()

    def _try_db(self) -> None:
        try:
            from collect import load_dotenv
            from collection_lib.migrations import apply_migrations
            from collection_lib.repository import CollectionRepository, open_local_connection

            load_dotenv()
            connection = open_local_connection()
            apply_migrations(connection)
            connection.commit()
            self.repository = CollectionRepository(connection)
        except Exception as exc:  # noqa: BLE001
            self.db_error = str(exc).split("using password")[0].strip()

    def _build(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)
        collect = ttk.Frame(notebook)
        site = ttk.Frame(notebook)
        ops = ttk.Frame(notebook)
        notebook.add(collect, text="采集数据")
        notebook.add(site, text="网站配置")
        notebook.add(ops, text="合作运维")
        inner = ttk.Notebook(collect)
        inner.pack(fill=tk.BOTH, expand=True)
        for key, title in COLLECT_PAGES:
            page = WorkPage(inner, key, title)
            inner.add(page, text=title)
            self.pages[key] = page
            self.workspaces.append(CollectionWorkspace(self, page, KIND_BY_PAGE[key], self.sources_path))
        site_page = WorkPage(site, "site_config", "网站配置")
        site_page.pack(fill=tk.BOTH, expand=True)
        self.pages["site_config"] = site_page
        self.workspaces.append(SiteConfigWorkspace(self, site_page))
        ops_page = WorkPage(ops, "operations", "合作运维")
        ops_page.pack(fill=tk.BOTH, expand=True)
        self.pages["operations"] = ops_page
        self.workspaces.append(OperationsWorkspace(self, ops_page))
        if self.db_error:
            self.log("operations", f"数据库不可用：{self.db_error}")
            self.log("collect.shops", f"数据库不可用：{self.db_error}")
        elif self.repository:
            for key, page in self.pages.items():
                for row in reversed(self.repository.recent_activity(key) or []):
                    page.write_log(f"{row.get('created_at')} {row.get('message')}")

    def log(self, page_key: str, message: str) -> None:
        line = self.logs.append(page_key, message)
        page = self.pages.get(page_key)
        if page:
            page.write_log(line)
        if self.repository:
            try:
                self.repository.append_activity(page_key, "log", message)
                self.repository.commit()
            except Exception:
                self.repository.rollback()

    def run_action(self, page_key: str, action: str, fn) -> None:
        def on_event(kind, _action, payload):
            if kind == "start":
                self.log(page_key, f"开始 {action}")
            elif kind == "busy":
                self.log(page_key, f"{action} 已在运行")
            elif kind == "ok":
                self.log(page_key, f"完成 {action}: {payload}")
            elif kind == "err":
                self.log(page_key, f"失败 {action}: {payload}")

        self.runner.submit(f"{page_key}:{action}", fn, on_event)


def main() -> int:
    root = tk.Tk()
    ConsoleApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
