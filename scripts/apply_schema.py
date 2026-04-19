"""
Apply data/db-schema.sql using credentials from app/.env (or process env).

Uses the mysql client program (same as `mysql < file.sql`) so multi-statement
scripts run reliably on Windows.

Run from repository root:
    python scripts/apply_schema.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / "app" / ".env"
SCHEMA_FILE = REPO_ROOT / "data" / "db-schema.sql"


def _mysql_cli() -> str:
    env_path = os.getenv("MYSQL_CLI")
    if env_path and Path(env_path).is_file():
        return env_path
    found = shutil.which("mysql")
    if found:
        return found
    default = Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")
    if default.is_file():
        return str(default)
    return "mysql"


def main() -> int:
    load_dotenv(ENV_FILE)
    if not SCHEMA_FILE.is_file():
        print(f"Schema file not found: {SCHEMA_FILE}", file=sys.stderr)
        return 1

    password = (os.getenv("DB_PASSWORD") or "").strip()
    if not password or password == "your_password":
        print(
            "Set DB_PASSWORD in app/.env (copy from app/.env.example) before running this script.",
            file=sys.stderr,
        )
        return 1

    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    port = os.getenv("DB_PORT", "3306")

    mysql_bin = _mysql_cli()
    cmd = [
        mysql_bin,
        f"--host={host}",
        f"--port={port}",
        f"--user={user}",
        f"--password={password}",
        "--default-character-set=utf8mb4",
    ]

    sql_bytes = SCHEMA_FILE.read_bytes()
    try:
        subprocess.run(cmd, input=sql_bytes, check=True, capture_output=True)
    except FileNotFoundError:
        print(
            "mysql client not found. Install MySQL Shell/Client or set MYSQL_CLI to mysql.exe.",
            file=sys.stderr,
        )
        return 1
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        if err:
            print(err, file=sys.stderr)
        print("Schema apply failed (check DB credentials and server).", file=sys.stderr)
        return exc.returncode or 1

    print("Schema applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
