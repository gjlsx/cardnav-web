"""Small operator GUI: collect tab and merge tab, each with its own log."""
from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .catch_config import configured_sources
from .gui_commands import MODULE_TABS, SOURCE_SHORT_LABELS, button_label, cli_argv

REPO_ROOT = Path(__file__).resolve().parents[2]


class CliJobs:
    def __init__(self) -> None:
        self._procs: dict[str, subprocess.Popen[str]] = {}

    def running(self, key: str) -> bool:
        proc = self._procs.get(key)
        return proc is not None and proc.poll() is None

    def start(self, key: str, argv: list[str], write) -> None:
        if self.running(key):
            write(f"{key} 已在运行")
            return
        proc = subprocess.Popen(
            argv,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._procs[key] = proc
        write(f"启动 {' '.join(argv[3:])}")
        threading.Thread(target=self._pump, args=(key, proc, write), daemon=True).start()

    def stop(self, key: str, write) -> None:
        proc = self._procs.get(key)
        if proc is None or proc.poll() is not None:
            write(f"{key} 未在运行")
            return
        proc.terminate()
        write(f"已停止 {key}")

    def _pump(self, key: str, proc: subprocess.Popen[str], write) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            text = line.strip()
            if text:
                write(text)
        code = proc.wait()
        write(f"{key} 退出 {code}")


class ModuleTab(ttk.Frame):
    def __init__(self, master: tk.Widget, module_key: str, actions: tuple[str, ...], jobs: CliJobs) -> None:
        super().__init__(master)
        self.jobs = jobs
        for source in configured_sources():
            row = ttk.Frame(self)
            row.pack(fill=tk.X, padx=8, pady=4)
            ttk.Label(row, text=SOURCE_SHORT_LABELS[source.source_id], width=8).pack(side=tk.LEFT)
            for action in actions:
                if action.endswith("-stop"):
                    ttk.Button(row, text=button_label(action, source.source_id), command=lambda sid=source.source_id, act=action: self._stop(act, sid)).pack(side=tk.LEFT, padx=3)
                else:
                    ttk.Button(row, text=button_label(action, source.source_id), command=lambda sid=source.source_id, act=action: self._start(act, sid)).pack(side=tk.LEFT, padx=3)
        self.log = ScrolledText(self, height=18, wrap="word")
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def write(self, line: str) -> None:
        self.after(0, self._append, line)

    def _append(self, line: str) -> None:
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)

    def _start(self, action: str, source_id: str) -> None:
        self.jobs.start(f"{action}:{source_id}", cli_argv(action, source_id), self.write)

    def _stop(self, action: str, source_id: str) -> None:
        job_key = f"{action.replace('-stop', '')}:{source_id}"
        self.jobs.stop(job_key, self.write)


def main() -> int:
    root = tk.Tk()
    root.title("PriceAI 采集")
    root.minsize(920, 540)
    jobs = CliJobs()
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    for module_key, title, actions in MODULE_TABS:
        tab = ModuleTab(notebook, module_key, actions, jobs)
        notebook.add(tab, text=title)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    raise SystemExit(main())
