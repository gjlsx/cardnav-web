"""Collection workspace: sources, manual run, record-level manual flags."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any
from pathlib import Path

from collection_lib.config import load_sources, normalize_source, validate_sources
from collection_lib.contracts import OverrideState, RecordKind
from collection_lib.fetch import fetch_approved_json
from collection_lib.fixtures import fixtures_for_source
from collection_lib.pipeline import run_source_pipeline
from collection_lib.publisher import PublicPublisher
from collection_lib.config import source_may_request_network, apply_item_cap
from console_lib.source_control import SourceRunControl
from console_lib.source_test import run_source_test

KIND_BY_PAGE = {
    "collect.gateway": RecordKind.GATEWAY_SITE,
    "collect.shops": RecordKind.SHOP_PRODUCT,
    "collect.official": RecordKind.OFFICIAL_PLAN,
    "collect.leaderboard": RecordKind.MODEL_RANK,
}


class CollectionWorkspace:
    def __init__(self, app, page, kind: RecordKind, sources_path):
        self.app = app
        self.page = page
        self.kind = kind
        self.sources_path = sources_path
        self.control = SourceRunControl()
        self.sources: list[dict[str, Any]] = []
        self._build()
        self.reload()

    def _build(self) -> None:
        ttk.Button(self.page.left, text="刷新", command=self.reload).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="抓取一次选中来源", command=self.manual_run).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="开始循环抓取选中来源", command=self.start_scheduler).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="停止选中来源", command=self.stop_scheduler).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="测试选中来源", command=self.test_source).pack(fill=tk.X, padx=6, pady=2)
        self.source_list = tk.Listbox(self.page.left, height=12)
        self.source_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        form = ttk.Frame(self.page.right)
        form.pack(fill=tk.X, padx=6, pady=4)
        self.vars = {key: tk.StringVar() for key in ("id", "name", "source_class", "target_domain", "priority", "interval_minutes", "max_items_per_run", "approval_status", "public_url")}
        self.enabled = tk.BooleanVar()
        row = 0
        for key in self.vars:
            ttk.Label(form, text=key).grid(row=row, column=0, sticky="w")
            ttk.Entry(form, textvariable=self.vars[key], width=42).grid(row=row, column=1, sticky="we")
            row += 1
        ttk.Checkbutton(form, text="enabled（仅调度；手工运行忽略）", variable=self.enabled).grid(row=row, column=1, sticky="w")
        btns = ttk.Frame(self.page.right)
        btns.pack(fill=tk.X, padx=6)
        ttk.Button(btns, text="保存来源", command=self.save_source).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="校验", command=self.validate).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="手工锁定选中记录", command=lambda: self.flag(OverrideState.MANUAL)).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="隐藏选中记录", command=lambda: self.flag(OverrideState.HIDDEN)).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="取消手工标志", command=self.clear_flag).pack(side=tk.LEFT, padx=3)
        self.records = tk.Listbox(self.page.right, height=12)
        self.records.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.source_list.bind("<<ListboxSelect>>", lambda _e: self._load_form())

    def reload(self) -> None:
        self.sources = []
        if self.app.repository:
            try:
                self.sources = [normalize_source(item) for item in self.app.repository.list_sources()]
            except Exception as exc:  # noqa: BLE001
                self.app.log(self.page.page_key, f"读取来源失败：{exc}")
        if not self.sources:
            try:
                self.sources = load_sources(self.sources_path)
            except Exception as exc:  # noqa: BLE001
                self.app.log(self.page.page_key, f"读取 sources 文件失败：{exc}")
        self.source_list.delete(0, tk.END)
        for source in self.sources:
            self.source_list.insert(tk.END, f"{source.get('id')} [{source.get('approval_status')}] enabled={bool(source.get('enabled'))}")
        self.records.delete(0, tk.END)
        if self.app.repository:
            for row in self.app.repository.list_staging(self.kind.value):
                self.records.insert(tk.END, f"{row.get('record_key')} {row.get('publish_status')} {row.get('price')}")
        self.app.log(self.page.page_key, f"已刷新 {len(self.sources)} 个来源")

    def _selected_source(self) -> dict[str, Any] | None:
        if not self.source_list.curselection():
            return None
        return self.sources[int(self.source_list.curselection()[0])]

    def _load_form(self) -> None:
        source = self._selected_source()
        if not source:
            return
        for key, var in self.vars.items():
            var.set(str(source.get(key) or ""))
        self.enabled.set(bool(source.get("enabled")))

    def _read_form(self) -> dict[str, Any]:
        source = {
            "id": self.vars["id"].get().strip(),
            "name": self.vars["name"].get().strip(),
            "source_class": self.vars["source_class"].get().strip(),
            "target_domain": self.vars["target_domain"].get().strip(),
            "priority": int(self.vars["priority"].get() or 0),
            "interval_minutes": int(self.vars["interval_minutes"].get() or 60),
            "max_items_per_run": int(self.vars["max_items_per_run"].get() or 1000),
            "approval_status": self.vars["approval_status"].get().strip() or "draft",
            "public_url": self.vars["public_url"].get().strip(),
            "allowlist_urls": [self.vars["public_url"].get().strip()] if self.vars["public_url"].get().strip() else [],
            "enabled": bool(self.enabled.get()),
            "record_kind": self.kind.value,
        }
        return normalize_source(source)

    def save_source(self) -> None:
        source = self._read_form()
        if self.app.repository:
            self.app.repository.upsert_source(source)
            self.app.repository.commit()
        self.app.log(self.page.page_key, f"已保存来源 {source['id']}")
        self.reload()

    def validate(self) -> None:
        errors = validate_sources([self._read_form()])
        if errors:
            messagebox.showerror("配置无效", "\n".join(errors))
            return
        messagebox.showinfo("配置有效", "来源校验通过。")

    def manual_run(self) -> None:
        source = self._selected_source() or self._read_form()

        self._launch(source, "manual")

    def _launch(self, source: dict[str, Any], trigger: str) -> None:
        source_id = str(source["id"])
        stop_flag = self.control.begin(source_id)
        if stop_flag is None:
            self.app.log(self.page.page_key, f"{source_id} 已在运行")
            return

        def job():
            try:
                if source_may_request_network(source):
                    body, rows, content_type = fetch_approved_json(source)
                else:
                    rows = fixtures_for_source(source["id"])
                    body = json.dumps(rows, ensure_ascii=False)
                    content_type = "application/json"
                rows = apply_item_cap(rows, int(source.get("max_items_per_run") or 0))
                return run_source_pipeline(self.app.repository, source, body, rows, content_type, trigger, self.kind, PublicPublisher(), should_stop=stop_flag.is_set)
            finally:
                self.control.finish(source_id)

        self.app.run_action(self.page.page_key, f"collect:{source_id}", job)

    def _selected_key(self) -> str | None:
        if not self.records.curselection():
            return None
        return str(self.records.get(self.records.curselection()[0])).split()[0]

    def flag(self, state: OverrideState) -> None:
        key = self._selected_key()
        if not key or not self.app.repository:
            return
        if not messagebox.askokcancel("确认", f"将 {key} 设为 {state.value}？取消后需重新采集。"):
            return
        self.app.repository.set_manual_override(self.kind, key, state)
        self.app.repository.commit()
        self.app.log(self.page.page_key, f"{key} -> {state.value}")

    def start_scheduler(self) -> None:
        source = self._selected_source()
        if not source:
            return
        source_id = str(source["id"])
        self.control.start_loop(source_id)
        self.app.log(self.page.page_key, f"已开始循环抓取 {source_id}")
        self._loop(source)

    def stop_scheduler(self) -> None:
        source = self._selected_source()
        if source:
            self.app.log(self.page.page_key, self.control.stop(str(source["id"])))

    def _loop(self, source: dict[str, Any]) -> None:
        source_id = str(source["id"])
        if not self.control.is_looping(source_id):
            return
        self._launch(source, "scheduler")
        delay = max(1, int(source.get("interval_minutes") or 60)) * 60 * 1000
        self.app.root.after(delay, lambda: self._loop(source))

    def test_source(self) -> None:
        source = self._selected_source() or self._read_form()
        source_id = str(source.get("id") or "")
        if not source_id:
            self.app.log(self.page.page_key, "测试失败：未选择来源")
            return

        def job():
            return run_source_test(Path(__file__).resolve().parents[1], source_id)

        self.app.run_action(self.page.page_key, f"test:{source_id}", job)

    def clear_flag(self) -> None:
        key = self._selected_key()
        if not key or not self.app.repository:
            return
        if not messagebox.askokcancel("确认", f"取消 {key} 手工标志？不会立即回填旧自动数据。"):
            return
        self.app.repository.clear_manual_override(self.kind, key)
        self.app.repository.commit()
        self.app.log(self.page.page_key, f"已取消 {key} 手工标志")
