"""Restore the last remote ailovemoney dump in BACKUP_DIR. Used only if a publish import fails."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vps_session import BACKUP_DIR, Session, connect, load_remote_mysql_password  # noqa: E402


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else "20260830-050729"
    dump = f"{BACKUP_DIR}/ailovemoney-{stamp}.sql"
    mysql_password = load_remote_mysql_password()
    client = connect()
    session = Session(client, mysql_password)
    try:
        session.run(f"test -s {dump} && echo dump_ok")
        session.run(
            f"mysql --host=127.0.0.1 --port=3306 --user=root --default-character-set=utf8mb4 < {dump}",
            timeout=300,
            env={"MYSQL_PWD": mysql_password},
            hide=mysql_password,
        )
        session.run(
            "mysql --host=127.0.0.1 --port=3306 --user=root -N -e "
            "\"SELECT COUNT(*) FROM ailovemoney.public_snapshot_entries; SELECT COUNT(*) FROM ailovemoney.gateway_sites;\"",
            env={"MYSQL_PWD": mysql_password},
            hide=mysql_password,
        )
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
