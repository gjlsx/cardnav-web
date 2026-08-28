"""Write whitelist observations to MySQL staging. Never prints connection secrets."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .whitelist import ALLOWED_FIELDS, filter_observation

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS collection_staging_observations (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  run_id VARCHAR(64) NOT NULL,
  normalized_site VARCHAR(255) NOT NULL DEFAULT '',
  source_id VARCHAR(64) NOT NULL DEFAULT '',
  source_class VARCHAR(32) NOT NULL DEFAULT '',
  source_priority INT NOT NULL DEFAULT 0,
  platform_family VARCHAR(100) NOT NULL DEFAULT '',
  model_or_plan VARCHAR(255) NOT NULL DEFAULT '',
  price DECIMAL(18,6) NULL,
  currency VARCHAR(16) NOT NULL DEFAULT '',
  billing_unit VARCHAR(64) NOT NULL DEFAULT '',
  stock_status VARCHAR(32) NOT NULL DEFAULT '',
  region VARCHAR(32) NOT NULL DEFAULT '',
  payment_tags VARCHAR(255) NOT NULL DEFAULT '',
  delivery_tags VARCHAR(255) NOT NULL DEFAULT '',
  public_perf VARCHAR(255) NOT NULL DEFAULT '',
  observed_at VARCHAR(64) NOT NULL DEFAULT '',
  provenance VARCHAR(255) NOT NULL DEFAULT '',
  confidence DECIMAL(6,3) NULL,
  KEY collection_staging_run (run_id),
  KEY collection_staging_site (normalized_site)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def mysql_bin() -> str:
    candidates = [
        os.environ.get("MYSQL_CLIENT"),
        r"D:\phpStudy\MySQL\bin\mysql.exe",
        "mysql",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.name.lower() == "mysql.exe" and path.exists():
            return str(path)
        if candidate == "mysql":
            return "mysql"
    return "mysql"


def mysql_base_args() -> list[str]:
    return [
        mysql_bin(),
        "--host", os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "--port", str(os.environ.get("MYSQL_PORT", "3306")),
        "--user", os.environ.get("MYSQL_USER", "root"),
        os.environ.get("MYSQL_DATABASE", "ailovemoney"),
        "--batch",
        "--raw",
        "--default-character-set=utf8mb4",
    ]


def run_mysql(sql: str) -> str:
    env = os.environ.copy()
    password = env.get("MYSQL_PASSWORD") or env.get("MYSQL_PWD") or ""
    if password:
        env["MYSQL_PWD"] = password
    completed = subprocess.run(
        mysql_base_args(),
        input=sql,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "mysql failed").split("using password")[0].strip())
    return completed.stdout


def ensure_staging_table() -> None:
    run_mysql(CREATE_SQL)


def write_staging(run_id: str, rows: list[dict[str, Any]]) -> dict[str, int]:
    ensure_staging_table()
    cleaned = [filter_observation(row) for row in rows]
    run_mysql("DELETE FROM collection_staging_observations WHERE run_id = '%s'" % run_id.replace("'", ""))
    for row in cleaned:
        columns = list(ALLOWED_FIELDS)
        values = []
        for column in columns:
            value = row.get(column)
            if value is None:
                values.append("NULL")
            else:
                text = str(value).replace("\\", "\\\\").replace("'", "\\'")
                values.append("'%s'" % text)
        sql = (
            "INSERT INTO collection_staging_observations (run_id, %s) VALUES ('%s', %s)"
            % (", ".join(columns), run_id.replace("'", ""), ", ".join(values))
        )
        run_mysql(sql)
    count_out = run_mysql(
        "SELECT COUNT(*) FROM collection_staging_observations WHERE run_id = '%s'" % run_id.replace("'", "")
    )
    count = int(count_out.strip().splitlines()[-1])
    return {"written": len(cleaned), "staging_count": count}


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(filter_observation(row), ensure_ascii=False) + "\n")
