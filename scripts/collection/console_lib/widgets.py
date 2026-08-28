"""Shared Tk layout: left list, right detail, bottom page log."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class WorkPage(ttk.Frame):
    def __init__(self, master, page_key: str, title: str):
        super().__init__(master)
        self.page_key = page_key
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=title, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        pane.grid(row=1, column=0, sticky="nsew", padx=8)
        self.left = ttk.Frame(pane, width=280)
        self.right = ttk.Frame(pane)
        pane.add(self.left, weight=1)
        pane.add(self.right, weight=3)
        self.log = ScrolledText(self, height=10, wrap="word")
        self.log.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        self.rowconfigure(2, weight=0)

    def write_log(self, line: str) -> None:
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
