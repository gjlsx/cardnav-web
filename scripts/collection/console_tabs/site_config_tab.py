"""Website config tab: exact public-row edit and hide."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from collection_lib.contracts import RecordKind
from collection_lib.public_data import hide_row, list_public_rows, save_manual_row


def parse_editor_payload(row: dict, editor_text: str) -> dict:
    """Apply editable key=value lines without accepting arbitrary storage fields."""
    payload = dict(row)
    for raw_line in editor_text.splitlines():
        key, separator, value = raw_line.partition("=")
        if separator and key in payload:
            payload[key] = value
    return payload


class SiteConfigWorkspace:
    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.kind = tk.StringVar(value=RecordKind.SHOP_PRODUCT.value)
        self._build()
        self.reload()

    def _build(self) -> None:
        ttk.Label(self.page.left, text="实体类型").pack(anchor="w", padx=6)
        combo = ttk.Combobox(self.page.left, textvariable=self.kind, values=[kind.value for kind in RecordKind], state="readonly")
        combo.pack(fill=tk.X, padx=6, pady=4)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.reload())
        ttk.Button(self.page.left, text="刷新", command=self.reload).pack(fill=tk.X, padx=6, pady=2)
        self.listbox = tk.Listbox(self.page.left, height=22)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        ttk.Label(self.page.right, text="site.score 是展示排序；来源 priority 不覆盖它。").pack(anchor="w", padx=6)
        self.editor = tk.Text(self.page.right, height=16, wrap="word")
        self.editor.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        btns = ttk.Frame(self.page.right)
        btns.pack(fill=tk.X, padx=6)
        ttk.Button(btns, text="保存手工覆盖", command=self.save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="隐藏", command=self.hide).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="取消手工标志", command=self.clear).pack(side=tk.LEFT, padx=4)
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._show())
        self.rows = []

    def reload(self) -> None:
        self.listbox.delete(0, tk.END)
        self.rows = []
        if not self.app.repository:
            self.app.log(self.page.page_key, "无数据库，无法加载正式数据")
            return
        kind = RecordKind(self.kind.get())
        self.rows = list_public_rows(self.app.repository, kind)
        for row in self.rows:
            self.listbox.insert(tk.END, row.get("record_key"))
        self.app.log(self.page.page_key, f"已加载 {len(self.rows)} 条 {kind.value}")

    def _selected(self):
        if not self.listbox.curselection():
            return None
        return self.rows[int(self.listbox.curselection()[0])]

    def _show(self) -> None:
        row = self._selected()
        if not row:
            return
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", "\n".join(f"{key}={row[key]}" for key in row))

    def save(self) -> None:
        row = self._selected()
        if not row or not self.app.repository:
            return
        payload = parse_editor_payload(row, self.editor.get("1.0", "end-1c"))
        payload["normalized_site"] = str(row.get("host") or row.get("site_id") or "").replace("collected-", "")
        payload["model_or_plan"] = str(row.get("standard_product") or row.get("model_name") or row.get("url_slug") or "")
        save_manual_row(self.app.repository, RecordKind(self.kind.get()), payload)
        self.app.log(self.page.page_key, f"已手工保存 {row.get('record_key')}")

    def hide(self) -> None:
        row = self._selected()
        if not row or not messagebox.askokcancel("确认隐藏", "隐藏不是物理删除。"):
            return
        hide_row(self.app.repository, RecordKind(self.kind.get()), row["record_key"])
        self.app.log(self.page.page_key, f"已隐藏 {row['record_key']}")
        self.reload()

    def clear(self) -> None:
        row = self._selected()
        if not row or not messagebox.askokcancel("确认", "取消后需重新采集，不会回填旧自动数据。"):
            return
        self.app.repository.clear_manual_override(RecordKind(self.kind.get()), row["record_key"])
        self.app.repository.commit()
        self.app.log(self.page.page_key, f"已取消 {row['record_key']}")
