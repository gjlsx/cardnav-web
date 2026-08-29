"""Paramiko session for ai.lovemoney.live on 206.119.177.74. Secrets stay in local files."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import paramiko

HOST = "206.119.177.74"
USER = "root"
CRED_FILE = Path(r"D:\temp\aws\177.74 server.txt")
LIKESHOP_CONFIG = Path(r"D:\phpStudy\WWW\likeshop\scripts\deploy_vps.config.ps1")
WEB_ROOT = "/www/wwwroot/ai.lovemoney.live"
BACKUP_DIR = "/www/wwwroot/ai.lovemoney.live-backups"


def load_vps_password() -> str:
    password = None
    for raw in CRED_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if ":" in line and any(k in lower for k in ("pwd", "pass", "password")):
            password = line.split(":", 1)[1].strip()
            break
    if not password:
        lines = [ln.strip() for ln in CRED_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
        password = lines[-1]
    if not password:
        raise RuntimeError("missing VPS password from local credential file")
    return password


def load_remote_mysql_password() -> str:
    text = LIKESHOP_CONFIG.read_text(encoding="utf-8")
    match = re.search(r"Remote\s*=\s*@\{.*?MysqlPassword\s*=\s*'([^']*)'", text, re.S)
    if not match:
        raise RuntimeError("could not parse remote MySQL password from local LikeShop deploy config")
    return match.group(1)


class Session:
    def __init__(self, client: paramiko.SSHClient, mysql_password: str):
        self.client = client
        self.mysql_password = mysql_password

    def run(self, command: str, timeout: int = 120, env: dict[str, str] | None = None, hide: str | None = None) -> str:
        shown = command if hide is None else command.replace(hide, "***")
        print(f"\n$ {shown}", flush=True)
        prefix = ""
        if env:
            parts = []
            for key, value in env.items():
                escaped = value.replace("'", "'\"'\"'")
                parts.append(f"export {key}='{escaped}'")
            prefix = "; ".join(parts) + "; "
        chan = self.client.get_transport().open_session()
        chan.set_combine_stderr(True)
        chan.exec_command(prefix + command)
        chunks: list[str] = []
        deadline = time.time() + timeout
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode("utf-8", "replace")
                chunks.append(data)
                sys.stdout.write(data)
                sys.stdout.flush()
                continue
            if chan.exit_status_ready():
                while chan.recv_ready():
                    data = chan.recv(4096).decode("utf-8", "replace")
                    chunks.append(data)
                    sys.stdout.write(data)
                    sys.stdout.flush()
                break
            if time.time() > deadline:
                chan.close()
                raise TimeoutError(f"command timed out after {timeout}s: {shown}")
            time.sleep(0.15)
        code = chan.recv_exit_status()
        if code != 0:
            raise RuntimeError(f"exit {code}: {shown}")
        return "".join(chunks)


def connect() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("[session] connect", flush=True)
    client.connect(
        hostname=HOST,
        username=USER,
        password=load_vps_password(),
        timeout=30,
        banner_timeout=60,
        auth_timeout=30,
        look_for_keys=False,
        allow_agent=False,
    )
    transport = client.get_transport()
    if transport is not None:
        transport.set_keepalive(15)
    return client
