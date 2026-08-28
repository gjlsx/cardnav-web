"""Controlled backup/restore/publish actions. Commands are allowlisted; secrets stay in env."""
from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EXPORT_SCRIPT = REPO / "scripts" / "export-mysql.ps1"
IMPORT_SCRIPT = REPO / "scripts" / "import-mysql.ps1"
HOWTO = REPO / "howtorunvpsnew.md"


def preview(action: str) -> str:
    if action == "backup":
        return f"将导出本机 ailovemoney 到 D:\\temp\\ailovemoney-console-backup.sql（使用 {EXPORT_SCRIPT.name}）"
    if action == "restore":
        return f"将从 D:\\temp\\ailovemoney-console-backup.sql 导入本机 ailovemoney（{IMPORT_SCRIPT.name}）"
    if action == "publish":
        return f"按 {HOWTO.name} 构建 dist 并尝试发布 ai.lovemoney.live；不改 LikeShop 8086/8090/8095，不编辑 SSH 密码。"
    raise ValueError("unknown action")


def run_confirmed(action: str, confirm_phrase: str) -> str:
    expected = {
        "backup": "CONFIRM BACKUP LOCAL MYSQL",
        "restore": "CONFIRM RESTORE LOCAL MYSQL",
        "publish": "CONFIRM PUBLISH AI.LOVEMONEY.LIVE",
    }
    if confirm_phrase != expected[action]:
        raise ValueError("confirmation mismatch; cancelled")
    env = os.environ.copy()
    if action == "backup":
        out = Path(r"D:\temp\ailovemoney-console-backup.sql")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(EXPORT_SCRIPT), "-OutputPath", str(out)],
            capture_output=True, text=True, env=env, cwd=str(REPO),
        )
        return _ok(completed)
    if action == "restore":
        src = Path(r"D:\temp\ailovemoney-console-backup.sql")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(IMPORT_SCRIPT), "-SqlPath", str(src)],
            capture_output=True, text=True, env=env, cwd=str(REPO),
        )
        return _ok(completed)
    completed = subprocess.run(
        ["pnpm", "run", "build"], capture_output=True, text=True, env=env, cwd=str(REPO),
    )
    if completed.returncode != 0:
        return _ok(completed)
    publish = Path(r"D:\temp\ailovemoney-p005\publish_p008.py")
    if not publish.exists():
        return "build ok; publish helper missing. Follow howtorunvpsnew.md manually. LikeShop ports were not touched."
    published = subprocess.run(["python", str(publish)], capture_output=True, text=True, env=env, cwd=str(REPO))
    return f"build ok\n{_ok(published)}"


def _ok(completed: subprocess.CompletedProcess) -> str:
    text = (completed.stdout or "") + "\n" + (completed.stderr or "")
    for secret in ("password", "MYSQL_PWD"):
        text = text.replace(os.environ.get(secret, "___never___"), "***")
    if completed.returncode != 0:
        raise RuntimeError(text.strip()[:1500] or f"exit {completed.returncode}")
    return text.strip()[:1500] or "ok"
