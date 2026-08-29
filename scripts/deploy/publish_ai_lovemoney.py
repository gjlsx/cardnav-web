"""Standard publish: pack local dist, export local ailovemoney SQL, backup origin, extract, import SQL, restart.

Does not upload .env and does not touch LikeShop 8086/8090/8095.
Credentials are read from local secure files documented in howtorunvpsnew.md.

Usage from repo root after pnpm test / typecheck / build:

    python scripts/deploy/publish_ai_lovemoney.py
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "deploy"))

from vps_session import (  # noqa: E402
    BACKUP_DIR,
    WEB_ROOT,
    Session,
    connect,
    load_dotenv,
    load_remote_mysql_password,
)

REMOTE_DIR = "/tmp/ailovemoney-publish"
EXPORT_SCRIPT = ROOT / "scripts" / "export-mysql.ps1"


def pack_dist(dest: Path) -> None:
    entry = ROOT / "dist" / "server" / "entry.mjs"
    if not entry.exists():
        raise SystemExit("local dist/server/entry.mjs missing; run pnpm run build first")
    if dest.exists():
        dest.unlink()
    subprocess.run(["tar", "-czf", str(dest), "dist"], cwd=ROOT, check=True)
    print(f"[pack] dist {dest.stat().st_size} bytes", flush=True)


def export_sql(dest: Path) -> None:
    local = load_dotenv(ROOT / ".env")
    env = os.environ.copy()
    if local.get("MYSQL_PASSWORD"):
        env["MYSQL_PASSWORD"] = local["MYSQL_PASSWORD"]
        env["MYSQL_PWD"] = local["MYSQL_PASSWORD"]
    for key in ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_DATABASE"):
        if local.get(key):
            env[key] = local[key]
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(EXPORT_SCRIPT),
            "-OutputPath",
            str(dest),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    raw = dest.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        dest.write_bytes(raw[3:])
    print(f"[export] sql {dest.stat().st_size} bytes", flush=True)


def connect_with_retry():
    last_error = None
    for attempt in range(1, 5):
        try:
            print(f"[session] attempt {attempt}", flush=True)
            return connect()
        except Exception as error:
            last_error = error
            print(f"[session] retry after {type(error).__name__}", flush=True)
            time.sleep(4 * attempt)
    raise last_error


def main() -> int:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    site_backup = f"{BACKUP_DIR}/ai.lovemoney.live-{stamp}.tar.gz"
    db_backup = f"{BACKUP_DIR}/ailovemoney-{stamp}.sql"
    mysql_password = load_remote_mysql_password()
    with tempfile.TemporaryDirectory(prefix="ailovemoney-publish-") as tmp:
        dist_tar = Path(tmp) / "dist.tar.gz"
        sql_path = Path(tmp) / "ailovemoney.sql"
        pack_dist(dist_tar)
        export_sql(sql_path)
        client = connect_with_retry()
        session = Session(client, mysql_password)
        try:
            session.run(f"mkdir -p {REMOTE_DIR} {BACKUP_DIR}")
            with client.open_sftp() as sftp:
                sftp.put(str(dist_tar), f"{REMOTE_DIR}/dist.tar.gz")
                sftp.put(str(sql_path), f"{REMOTE_DIR}/ailovemoney.sql")
                print("[sftp] uploaded dist and sql", flush=True)
            session.run(f"tar -C /www/wwwroot -czf {site_backup} ai.lovemoney.live", timeout=180)
            session.run(
                f"mysqldump --host=127.0.0.1 --port=3306 --user=root --single-transaction --routines --events "
                f"--default-character-set=utf8mb4 --databases ailovemoney > {db_backup}",
                timeout=300,
                env={"MYSQL_PWD": mysql_password},
                hide=mysql_password,
            )
            session.run(f"tar -xzf {REMOTE_DIR}/dist.tar.gz -C {WEB_ROOT}", timeout=120)
            session.run(f"test -f {WEB_ROOT}/dist/server/entry.mjs && echo dist_ok")
            session.run(f"test -f {WEB_ROOT}/.env && echo env_kept")
            session.run(
                "mysql --host=127.0.0.1 --port=3306 --user=root --default-character-set=utf8mb4 "
                f"< {REMOTE_DIR}/ailovemoney.sql",
                timeout=300,
                env={"MYSQL_PWD": mysql_password},
                hide=mysql_password,
            )
            session.run(
                "mysql --host=127.0.0.1 --port=3306 --user=root -N -e "
                "\"SELECT COUNT(*) FROM ailovemoney.public_snapshot_entries; "
                "SELECT COUNT(*) FROM ailovemoney.gateway_sites; "
                "SELECT COUNT(*) FROM ailovemoney.gateway_model_prices;\"",
                env={"MYSQL_PWD": mysql_password},
                hide=mysql_password,
            )
            session.run(f"chown -R www-data:www-data {WEB_ROOT}")
            session.run("systemctl restart ai-lovemoney; sleep 2; systemctl is-active apache2 ai-lovemoney")
            session.run("ss -lntp | grep -E ':80|:443|:3101|:8086|:8090|:8095' || true")
            session.run("ps aux | grep -E 'collection|collect.py|crawlee' | grep -v grep || echo no_collector")
            session.run("systemctl list-timers --all | grep -Ei 'collect|crawlee' || echo no_collect_timer")
            session.run("curl -sS -o /dev/null -w 'http80 %{http_code}\\n' --max-time 10 -H 'Host: ai.lovemoney.live' http://127.0.0.1/")
            session.run("curl -skS -o /dev/null -w 'https443 %{http_code}\\n' --max-time 10 --resolve ai.lovemoney.live:443:127.0.0.1 https://ai.lovemoney.live/")
            for path in ("/", "/shops", "/llm-gateway", "/official-price", "/model-leaderboard", "/guide"):
                session.run(
                    f"curl -skS -o /tmp/ai-page.html -w '{path} %{{http_code}} %{{size_download}}\\n' --max-time 20 "
                    f"--resolve ai.lovemoney.live:443:127.0.0.1 https://ai.lovemoney.live{path}"
                )
            session.run("curl -sS -o /dev/null -w 'shop_8086 %{http_code}\\n' --max-time 8 -H 'Host: dtch.yg2022.top' http://127.0.0.1:8086/shop/")
            session.run("curl -sS -o /dev/null -w 'mobile_8090 %{http_code}\\n' --max-time 8 -H 'Host: dtch.yg2022.top' http://127.0.0.1:8090/mobile/")
            session.run("curl -sS -o /dev/null -w 'admin_8095 %{http_code}\\n' --max-time 8 -H 'Host: dtch.yg2022.top' http://127.0.0.1:8095/admin/")
            session.run(f"rm -rf {REMOTE_DIR}")
            print(f"[done] site_backup={site_backup}", flush=True)
            print(f"[done] db_backup={db_backup}", flush=True)
            return 0
        finally:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
