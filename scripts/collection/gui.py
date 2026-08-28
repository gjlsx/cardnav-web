#!/usr/bin/env python3
"""Tkinter source editor and fixture dry-run, modeled after PriceAI-Monitor's local pane."""
from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collection_lib.config import load_sources, save_sources, validate_sources  # noqa: E402
from collect import cmd_dry_run  # noqa: E402

SOURCES_PATH = ROOT / "sources.json"
EXAMPLE_PATH = ROOT / "sources.example.json"


class CollectorGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI LoveMoney 本机采集（fixture / dry-run）")
        self.sources_path = SOURCES_PATH if SOURCES_PATH.exists() else EXAMPLE_PATH
        self.sources = load_sources(self.sources_path)
        self.current = 0
        self._build()
        self._load_into_form()

    def _build(self) -> None:
        left = ttk.Frame(self.root, padding=8)
        right = ttk.Frame(self.root, padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(left, text="来源").pack(anchor="w")
        self.listbox = tk.Listbox(left, height=16, width=36)
        self.listbox.pack(fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        form = ttk.Frame(right)
        form.pack(fill=tk.X)
        self.vars = {
            "id": tk.StringVar(),
            "name": tk.StringVar(),
            "source_class": tk.StringVar(),
            "target_domain": tk.StringVar(),
            "priority": tk.StringVar(),
            "interval_minutes": tk.StringVar(),
            "max_items_per_run": tk.StringVar(),
            "approval_status": tk.StringVar(),
        }
        self.enabled = tk.BooleanVar()
        row = 0
        for key, label in (
            ("id", "ID"),
            ("name", "名称"),
            ("source_class", "类别 site_api/site_html/aggregator"),
            ("target_domain", "目标域名"),
            ("priority", "priority"),
            ("interval_minutes", "interval_minutes"),
            ("max_items_per_run", "max_items_per_run (0=不限)"),
            ("approval_status", "批准 draft/approved"),
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w")
            ttk.Entry(form, textvariable=self.vars[key], width=48).grid(row=row, column=1, sticky="we")
            row += 1
        ttk.Checkbutton(form, text="enabled（调度用；手工 dry-run 会忽略）", variable=self.enabled).grid(row=row, column=1, sticky="w")
        buttons = ttk.Frame(right)
        buttons.pack(fill=tk.X, pady=8)
        ttk.Button(buttons, text="保存配置", command=self.save).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="校验", command=self.validate).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="手工 fixture dry-run", command=self.dry_run).pack(side=tk.LEFT, padx=4)
        ttk.Label(right, text="不会向未批准来源发 HTTP，也不会安装计划任务或自动发布。").pack(anchor="w")
        self.log = tk.Text(right, height=18, wrap="word")
        self.log.pack(fill=tk.BOTH, expand=True, pady=8)
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for source in self.sources:
            self.listbox.insert(tk.END, f"{source['id']} [{source['approval_status']}]")

    def _on_select(self, _event=None) -> None:
        if not self.listbox.curselection():
            return
        self._save_form_into_source()
        self.current = int(self.listbox.curselection()[0])
        self._load_into_form()

    def _load_into_form(self) -> None:
        source = self.sources[self.current]
        for key, var in self.vars.items():
            var.set(str(source.get(key, "")))
        self.enabled.set(bool(source.get("enabled")))

    def _save_form_into_source(self) -> None:
        source = self.sources[self.current]
        source["id"] = self.vars["id"].get().strip()
        source["name"] = self.vars["name"].get().strip()
        source["source_class"] = self.vars["source_class"].get().strip()
        source["target_domain"] = self.vars["target_domain"].get().strip()
        source["priority"] = int(self.vars["priority"].get() or 0)
        source["interval_minutes"] = int(self.vars["interval_minutes"].get() or 60)
        source["max_items_per_run"] = int(self.vars["max_items_per_run"].get() or 1000)
        source["approval_status"] = self.vars["approval_status"].get().strip() or "draft"
        source["enabled"] = bool(self.enabled.get())

    def save(self) -> None:
        self._save_form_into_source()
        target = SOURCES_PATH
        save_sources(target, self.sources)
        self.sources_path = target
        self.log.insert(tk.END, f"已保存 {target}\n")
        self._refresh_list()

    def validate(self) -> None:
        self._save_form_into_source()
        errors = validate_sources(self.sources)
        if errors:
            messagebox.showerror("配置无效", "\n".join(errors))
            return
        messagebox.showinfo("配置有效", f"{len(self.sources)} 条来源。默认 enabled=false, interval=60, max_items=1000。")

    def dry_run(self) -> None:
        self._save_form_into_source()
        save_sources(ROOT / "sources.runtime.json", self.sources)
        from io import StringIO
        buffer = StringIO()
        old = sys.stdout
        sys.stdout = buffer
        try:
            cmd_dry_run(ROOT / "sources.runtime.json", ignore_enabled=True)
        finally:
            sys.stdout = old
        self.log.delete("1.0", tk.END)
        self.log.insert("1.0", buffer.getvalue())


def main() -> int:
    if not SOURCES_PATH.exists() and EXAMPLE_PATH.exists():
        SOURCES_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    root = tk.Tk()
    CollectorGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
