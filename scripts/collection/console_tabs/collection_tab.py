"""Raw-first collection workspace: capture batches, audit, merge preview, and explicit import."""
from __future__ import annotations

import json
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable

from collection_lib.config import apply_item_cap, load_sources, normalize_source, source_may_request_network, validate_sources
from collection_lib.contracts import OverrideState, RecordKind
from collection_lib.fetch import fetch_approved_json
from collection_lib.fixtures import fixtures_for_source
from collection_lib.pipeline import SourceCapture, run_collection_batch
from collection_lib.runtime_import import RuntimeImporter, merge_raw_records
from console_lib.source_control import SourceRunControl
from console_lib.source_test import run_source_test

KIND_BY_PAGE = {
    "collect.gateway": RecordKind.GATEWAY_SITE,
    "collect.shops": RecordKind.SHOP_PRODUCT,
    "collect.official": RecordKind.OFFICIAL_PLAN,
    "collect.leaderboard": RecordKind.MODEL_RANK,
}


def source_capture(source: dict[str, Any], kind: RecordKind) -> SourceCapture:
    """Build a raw capture; HTTP is allowed only for approved allowlisted sources."""
    if source_may_request_network(source):
        body, rows, content_type = fetch_approved_json(source)
    else:
        rows = fixtures_for_source(str(source["id"]))
        body = json.dumps(rows, ensure_ascii=False)
        content_type = "application/json"
    return SourceCapture(
        source=source,
        body=body,
        rows=apply_item_cap(rows, int(source.get("max_items_per_run") or 0)),
        content_type=content_type,
        kind=kind,
    )


class CollectionWorkspace:
    view_names = ("来源与批次", "统一 raw 审计记录", "旧 staging 检查", "合并预览/冲突", "当前运行时记录")

    def __init__(self, app, page, kind: RecordKind, sources_path):
        self.app, self.page, self.kind, self.sources_path = app, page, kind, sources_path
        self.control = SourceRunControl()
        self.sources: list[dict[str, Any]] = []
        self.current_batch_id: str | None = None
        self._build()
        self.reload()

    def _build(self) -> None:
        ttk.Button(self.page.left, text="刷新全部视图", command=self.reload).pack(fill=tk.X, padx=6, pady=2)
        self.capture_button = ttk.Button(self.page.left, text="抓取选中来源（同一批次）", command=self.manual_run)
        self.capture_button.pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="开始循环抓取选中来源", command=self.start_scheduler).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="停止选中来源", command=self.stop_scheduler).pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(self.page.left, text="测试选中来源", command=self.test_source).pack(fill=tk.X, padx=6, pady=2)
        self.open_url_button = ttk.Button(self.page.left, text="打开已批准站点", command=self.open_site, state=tk.DISABLED)
        self.open_url_button.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(self.page.left, text="可多选；每次抓取生成一个 raw 批次").pack(anchor="w", padx=6, pady=(6, 0))
        self.source_list = tk.Listbox(self.page.left, height=12, selectmode=tk.EXTENDED, exportselection=False)
        self.source_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.source_list.bind("<<ListboxSelect>>", lambda _e: self._load_form())

        form = ttk.Frame(self.page.right)
        form.pack(fill=tk.X, padx=6, pady=4)
        form.columnconfigure(1, weight=1)
        keys = ("id", "name", "source_class", "target_domain", "priority", "interval_minutes", "max_items_per_run", "approval_status", "public_url")
        self.vars = {key: tk.StringVar() for key in keys}
        self.enabled = tk.BooleanVar()
        for row, key in enumerate(keys):
            ttk.Label(form, text=key).grid(row=row, column=0, sticky="w")
            ttk.Entry(form, textvariable=self.vars[key], width=52).grid(row=row, column=1, sticky="we")
        ttk.Checkbutton(form, text="enabled（只影响循环；手工抓取仍会执行）", variable=self.enabled).grid(row=len(keys), column=1, sticky="w")
        self.batch_summary = tk.StringVar(value="未选择批次；抓取只写原始数据，不会更新运行时数据。")
        ttk.Label(self.page.right, textvariable=self.batch_summary, foreground="#315b85").pack(anchor="w", padx=8, pady=(0, 4))

        buttons = ttk.Frame(self.page.right)
        buttons.pack(fill=tk.X, padx=6)
        ttk.Button(buttons, text="保存来源", command=self.save_source).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons, text="校验", command=self.validate).pack(side=tk.LEFT, padx=3)
        self.import_button = ttk.Button(buttons, text="合并并入库运行数据表", command=self.merge_import)
        self.import_button.pack(side=tk.LEFT, padx=12)
        ttk.Button(buttons, text="手工锁定选中 raw 记录", command=lambda: self.flag(OverrideState.MANUAL)).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons, text="隐藏选中 raw 记录", command=lambda: self.flag(OverrideState.HIDDEN)).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons, text="取消手工标志", command=self.clear_flag).pack(side=tk.LEFT, padx=3)

        self.views = ttk.Notebook(self.page.right)
        self.views.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.batch_list = self._view_list("来源与批次", self._on_batch_select)
        self.raw_list = self._view_list("统一 raw 审计记录")
        self.staging_list = self._view_list("旧 staging 检查")
        self.preview_list = self._view_list("合并预览/冲突")
        self.runtime_list = self._view_list("当前运行时记录")

    def _view_list(self, title: str, bind: Callable | None = None) -> tk.Listbox:
        frame = ttk.Frame(self.views)
        self.views.add(frame, text=title)
        box = tk.Listbox(frame, exportselection=False)
        box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        if bind:
            box.bind("<<ListboxSelect>>", bind)
        return box

    def reload(self) -> None:
        self._reload_sources()
        self._refresh_views()
        self.app.log(self.page.page_key, f"已刷新 {len(self.sources)} 个来源")

    def _reload_sources(self) -> None:
        self.sources = []
        if self.app.repository:
            try:
                self.sources = [normalize_source(item) for item in self.app.repository.list_sources() if item.get("record_kind") == self.kind.value]
            except Exception as exc:  # noqa: BLE001
                self.app.log(self.page.page_key, f"读取来源失败：{exc}")
        if not self.sources:
            try:
                self.sources = [item for item in load_sources(self.sources_path) if item.get("record_kind", self.kind.value) == self.kind.value]
            except Exception as exc:  # noqa: BLE001
                self.app.log(self.page.page_key, f"读取 sources 文件失败：{exc}")
        self.source_list.delete(0, tk.END)
        for source in self.sources:
            self.source_list.insert(tk.END, f"{source.get('id')} [{source.get('approval_status')}] enabled={bool(source.get('enabled'))}")

    def _refresh_views(self) -> None:
        for box in (self.batch_list, self.raw_list, self.staging_list, self.preview_list, self.runtime_list):
            box.delete(0, tk.END)
        if not self.app.repository:
            return
        batches = self.app.repository.list_batches(self.kind.value)
        valid_ids = {str(row["batch_id"]) for row in batches}
        if self.current_batch_id not in valid_ids:
            self.current_batch_id = str(batches[0]["batch_id"]) if batches else None
        for row in batches:
            self.batch_list.insert(tk.END, f"{row['batch_id']} | {row['status']} | raw={row['raw_count']} | sources={row['source_count']}")
        for row in self.app.repository.list_raw_records(self.kind.value, self.current_batch_id):
            self.raw_list.insert(tk.END, f"{row['record_key']} | {row['source_id']} | {row['validation_state']} | batch={row['batch_id']}")
        for row in self.app.repository.list_staging(self.kind.value):
            self.staging_list.insert(tk.END, f"{row['record_key']} | {row.get('source_id') or ''} | {row['publish_status']} | {row.get('price')}")
        if self.current_batch_id:
            for row in merge_raw_records(self.app.repository.fetch_raw_batch(self.current_batch_id)):
                self.preview_list.insert(tk.END, f"{row['record_key']} | winner={row['source_id']} | merged sources={row['source_rows']}")
        for row in self.app.repository.list_runtime_records(self.kind):
            self.runtime_list.insert(tk.END, f"{row['runtime_key']} | {row.get('source_id') or ''} | {row.get('label') or ''} | {row.get('value')}")
        self._update_batch_summary()

    def _update_batch_summary(self) -> None:
        if not self.current_batch_id or not self.app.repository:
            self.batch_summary.set("未选择批次；抓取只写原始数据，不会更新运行时数据。")
            return
        batch = self.app.repository.get_batch(self.current_batch_id) or {}
        count = len(self.app.repository.fetch_raw_batch(self.current_batch_id))
        status = str(batch.get("status") or "unknown")
        message = f"批次 {self.current_batch_id}：raw={count}，状态={status}。"
        message += "已入库运行数据表（已发布）。" if status == "imported" else "原始数据已入库，待合并并入库运行数据表。"
        self.batch_summary.set(message)

    def _selected_sources(self) -> list[dict[str, Any]]:
        return [self.sources[int(index)] for index in self.source_list.curselection()]

    def _selected_source(self) -> dict[str, Any] | None:
        selected = self._selected_sources()
        return selected[0] if selected else None

    def _load_form(self) -> None:
        source = self._selected_source()
        if source:
            for key, var in self.vars.items():
                var.set(str(source.get(key) or ""))
            self.enabled.set(bool(source.get("enabled")))
            allowed = bool(source.get("public_url")) and source_may_request_network(source)
            self.open_url_button.configure(state=tk.NORMAL if allowed else tk.DISABLED)

    def _read_form(self) -> dict[str, Any]:
        source = {
            "id": self.vars["id"].get().strip(), "name": self.vars["name"].get().strip(),
            "source_class": self.vars["source_class"].get().strip(), "target_domain": self.vars["target_domain"].get().strip(),
            "priority": int(self.vars["priority"].get() or 0), "interval_minutes": int(self.vars["interval_minutes"].get() or 60),
            "max_items_per_run": int(self.vars["max_items_per_run"].get() or 1000), "approval_status": self.vars["approval_status"].get().strip() or "draft",
            "public_url": self.vars["public_url"].get().strip(), "enabled": bool(self.enabled.get()), "record_kind": self.kind.value,
        }
        source["allowlist_urls"] = [source["public_url"]] if source["public_url"] else []
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
        else:
            messagebox.showinfo("配置有效", "来源校验通过。")

    def manual_run(self) -> None:
        sources = self._selected_sources() or ([self._read_form()] if self.vars["id"].get().strip() else [])
        if not sources:
            self.app.log(self.page.page_key, "抓取失败：请选择至少一个来源")
            return
        self._launch_batch(sources, "manual")

    def _launch_batch(self, sources: list[dict[str, Any]], trigger: str) -> None:
        flags = []
        for source in sources:
            flag = self.control.begin(str(source["id"]))
            if flag is None:
                for started in sources[:len(flags)]:
                    self.control.finish(str(started["id"]))
                self.app.log(self.page.page_key, f"{source['id']} 已在运行；未创建批次")
                return
            flags.append(flag)

        def job():
            try:
                return run_collection_batch(self.app.repository, [source_capture(source, self.kind) for source in sources], trigger=trigger, should_stop=lambda: any(flag.is_set() for flag in flags))
            finally:
                for source in sources:
                    self.control.finish(str(source["id"]))

        def succeeded(result):
            batch_id = result.get("batch_id") if isinstance(result, dict) else None
            if batch_id:
                self.current_batch_id = str(batch_id)
                self.app.log(self.page.page_key, f"原始数据已入库，待合并：{batch_id}")
            self._refresh_views()

        self.app.run_action(self.page.page_key, "collect-batch:" + ",".join(str(source["id"]) for source in sources), job, succeeded)

    def start_scheduler(self) -> None:
        sources = self._selected_sources()
        if not sources:
            self.app.log(self.page.page_key, "循环抓取失败：请选择来源")
            return
        for source in sources:
            source_id = str(source["id"])
            self.control.start_loop(source_id)
            self.app.log(self.page.page_key, f"已开始循环抓取 {source_id}")
            self._loop(source)

    def stop_scheduler(self) -> None:
        for source in self._selected_sources():
            self.app.log(self.page.page_key, self.control.stop(str(source["id"])))

    def _loop(self, source: dict[str, Any]) -> None:
        source_id = str(source["id"])
        if not self.control.is_looping(source_id):
            self.app.log(self.page.page_key, f"task {source_id} is stop!")
            return
        self._launch_batch([source], "scheduler")
        self.app.root.after(max(1, int(source.get("interval_minutes") or 60)) * 60 * 1000, lambda: self._loop(source))

    def test_source(self) -> None:
        source = self._selected_source() or (self._read_form() if self.vars["id"].get().strip() else None)
        if not source:
            self.app.log(self.page.page_key, "测试失败：未选择来源")
            return
        source_id = str(source["id"])
        self.app.run_action(self.page.page_key, f"test:{source_id}", lambda: run_source_test(Path(__file__).resolve().parents[1], source_id))

    def open_site(self) -> None:
        source = self._selected_source()
        if not source or not source_may_request_network(source) or not source.get("public_url"):
            self.app.log(self.page.page_key, "无法打开站点：未配置已批准的 public_url")
            return
        webbrowser.open_new_tab(str(source["public_url"]))
        self.app.log(self.page.page_key, f"已打开已批准站点：{source['id']}")

    def _on_batch_select(self, _event=None) -> None:
        if self.batch_list.curselection():
            self.current_batch_id = str(self.batch_list.get(self.batch_list.curselection()[0])).split(" | ")[0]
            self._refresh_views()

    def _selected_raw_key(self) -> str | None:
        return str(self.raw_list.get(self.raw_list.curselection()[0])).split(" | ")[0] if self.raw_list.curselection() else None

    def flag(self, state: OverrideState) -> None:
        key = self._selected_raw_key()
        if not key or not self.app.repository:
            self.app.log(self.page.page_key, "请选择一条统一 raw 审计记录")
            return
        if messagebox.askokcancel("确认手工标志", f"将 {key} 设为 {state.value}？以后自动合并会跳过该稳定键。"):
            self.app.repository.set_manual_override(self.kind, key, state)
            self.app.repository.commit()
            self.app.log(self.page.page_key, f"{key} -> {state.value}；raw 保留，后续自动合并跳过")

    def clear_flag(self) -> None:
        key = self._selected_raw_key()
        if not key or not self.app.repository:
            self.app.log(self.page.page_key, "请选择一条统一 raw 审计记录")
            return
        if messagebox.askokcancel("确认取消", f"取消 {key} 手工标志？不会立即回填，需再次合并。"):
            self.app.repository.clear_manual_override(self.kind, key)
            self.app.repository.commit()
            self.app.log(self.page.page_key, f"已取消 {key} 手工标志；可再次合并")

    def merge_import(self) -> None:
        batch_id = self.current_batch_id
        if not batch_id or not self.app.repository:
            self.app.log(self.page.page_key, "合并失败：请选择一个已完成 raw 批次")
            return
        batch = self.app.repository.get_batch(batch_id) or {}
        raw_count = len(self.app.repository.fetch_raw_batch(batch_id))
        if batch.get("status") != "raw_completed":
            self.app.log(self.page.page_key, f"合并不可用：批次 {batch_id} 状态为 {batch.get('status')}")
            return
        prompt = f"批次：{batch_id}\nraw 记录：{raw_count}\n\n确认后将合并、去重并事务写入运行数据表；该入库即发布。"
        if not messagebox.askokcancel("确认合并并入库运行数据表", prompt):
            self.app.log(self.page.page_key, f"已取消合并：{batch_id}")
            return

        def succeeded(_result):
            self.app.log(self.page.page_key, f"已合并并入库运行数据表：{batch_id}（已发布）")
            self._refresh_views()

        self.app.run_action(self.page.page_key, f"merge-import:{batch_id}", lambda: RuntimeImporter().merge_import_batch(self.app.repository, batch_id), succeeded)
