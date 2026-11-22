"""Read-only database connections for a SkillForge MCP server.

Copy the one function for the person's database into server.py (or keep this file next to
server.py and import it). Each function makes the *database itself* refuse writes for that
connection, so a query Claude writes can't change data even if it slips past a keyword check.
The real boundary is still a database user that has only SELECT rights: ask the DB owner for one
and say so in the README.

Patterns (ideas, not copied code): lukleh/mcp-read-only-sql (MIT) and
shibbirweb/mcp-mysql-read-only (MIT): session-level read-only, a statement timeout, one statement
per call, a row cap on what is returned.
"""

from __future__ import annotations

import os
import re

from mcp.server.mcpserver.exceptions import ToolError

MAX_ROWS = 200            # rows returned to Claude per call; say "더 있음" when cut
TIMEOUT_SECONDS = 30      # the database stops a query that runs longer
READ_SQL = re.compile(r"^\s*(select|with|show|describe|desc|explain)\b", re.I)


def check_sql(sql: str) -> str:
    """Refuse anything but one read statement. A guard only; the connection below enforces it."""
    body = sql.strip().rstrip(";")
    if ";" in body:
        raise ToolError("Only one statement per call.")
    if not READ_SQL.match(body):
        raise ToolError("Only SELECT / WITH / SHOW / DESCRIBE / EXPLAIN are allowed (read-only).")
    return body


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ToolError(f"Set the {name} environment variable first.")
    return value


# --- PostgreSQL (psycopg 3: requirements.txt `psycopg[binary]>=3.1`) ---------------------------
def connect_postgres(prefix: str):
    import psycopg

    conn = psycopg.connect(
        host=_env(f"{prefix}_HOST"), dbname=_env(f"{prefix}_DB"),
        user=_env(f"{prefix}_USER"), password=_env(f"{prefix}_PASSWORD"),
        port=int(os.environ.get(f"{prefix}_PORT", "5432")),
        # Every transaction on this connection is READ ONLY; a write fails inside the database.
        options=f"-c default_transaction_read_only=on -c statement_timeout={TIMEOUT_SECONDS * 1000}",
        connect_timeout=10,
        autocommit=True,  # one statement, one transaction: a failed query can't block the next one
    )
    return conn


# --- MySQL / MariaDB (PyMySQL: requirements.txt `pymysql>=1.1`) -------------------------------
def connect_mysql(prefix: str):
    import pymysql

    conn = pymysql.connect(
        host=_env(f"{prefix}_HOST"), database=_env(f"{prefix}_DB"),
        user=_env(f"{prefix}_USER"), password=_env(f"{prefix}_PASSWORD"),
        port=int(os.environ.get(f"{prefix}_PORT", "3306")),
        connect_timeout=10, read_timeout=TIMEOUT_SECONDS,
        # Autocommit ON on purpose: each statement is its own transaction, and the SESSION
        # setting below makes every one of them READ ONLY (a write fails with error 1792).
        # With autocommit OFF, `SET TRANSACTION READ ONLY` (no SESSION) lasts for one
        # transaction only and the next one can write.
        autocommit=True,
        init_command="SET SESSION TRANSACTION READ ONLY",
    )
    return conn


# --- SQLite (standard library) -----------------------------------------------------------------
def connect_sqlite(prefix: str):
    import sqlite3

    path = _env(f"{prefix}_PATH")
    # mode=ro: the file is opened read-only; query_only refuses writes even to temp tables.
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=TIMEOUT_SECONDS)
    conn.execute("PRAGMA query_only = ON")
    return conn


# --- SQL Server (pyodbc) / Snowflake / others ----------------------------------------------------
# These have no per-session "read only" switch that blocks writes. Use a login or role that has
# only SELECT (Snowflake: a role with USAGE + SELECT, set with role=... in connect()), keep
# check_sql() in front, and write that requirement in the README as
# [확인 필요: 조회 전용 계정 - DB 담당자]. SQL Server's ApplicationIntent=ReadOnly only routes to a
# replica; it does not block writes on its own.


def _plain(value):
    """Dates, decimals and bytes as text, so the tool result is plain JSON."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def fetch(conn, sql: str, params: tuple | dict = ()) -> dict:
    """Run one checked read statement with bound parameters; return at most MAX_ROWS rows.

    Put values the person gives (dates, store codes) in params, never into the SQL text.
    """
    cur = conn.cursor()
    try:
        cur.execute(check_sql(sql), params)
        cols = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(MAX_ROWS + 1)
    except ToolError:
        raise
    except Exception as exc:  # the database's own refusal or a timeout: show Claude why
        raise ToolError(f"The database refused or stopped the query: {exc}") from None
    finally:
        cur.close()
        try:
            conn.rollback()  # nothing to keep (read-only); clears a failed transaction
        except Exception:
            pass
    return {"columns": cols, "rows": [[_plain(v) for v in r] for r in rows[:MAX_ROWS]], "more": len(rows) > MAX_ROWS}
