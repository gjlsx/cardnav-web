"""Operations tab with mandatory second confirmation."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from console_lib.operations import preview, run_confirmed


class OperationsWorkspace:
    def __init__(self, app, page):
        self.app = app
        self.page = page
        ttk.Label(page.left, text="维护动作").pack(anchor="w", padx=6, pady=6)
        for action, label in (("backup", "备份本机 MySQL"), ("restore", "恢复本机 MySQL"), ("publish", "发布 ai.lovemoney.live")):
            ttk.Button(page.left, text=label, command=lambda a=action: self._run(a)).pack(fill=tk.X, padx=6, pady=3)
        ttk.Label(page.right, text="预检默认显示；二次确认后才执行。不提供 SSH 密码编辑。LikeShop 8086/8090/8095 禁止改动。").pack(anchor="w", padx=6, pady=6)

    def _run(self, action: str) -> None:
        summary = preview(action)
        self.app.log(self.page.page_key, f"预检 {action}: {summary}")
        phrases = {
            "backup": "CONFIRM BACKUP LOCAL MYSQL",
            "restore": "CONFIRM RESTORE LOCAL MYSQL",
            "publish": "CONFIRM PUBLISH AI.LOVEMONEY.LIVE",
        }
        if not messagebox.askokcancel("二次确认", f"{summary}\n\n确认请按确定，将要求精确确认短语。"):
            self.app.log(self.page.page_key, f"已取消 {action}")
            return
        from tkinter import simpledialog
        typed = simpledialog.askstring("确认短语", f"输入：{phrases[action]}")
        if typed != phrases[action]:
            self.app.log(self.page.page_key, f"确认短语不匹配，未执行 {action}")
            return
        self.app.run_action(self.page.page_key, action, lambda: run_confirmed(action, typed or ""))
