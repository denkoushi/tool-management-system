from __future__ import annotations

import psycopg2

from .config import DB_CONFIG


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def ensure_tables():
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users(
                  uid TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_master(
                  id BIGSERIAL PRIMARY KEY,
                  name TEXT UNIQUE NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tools(
                  uid TEXT PRIMARY KEY,
                  name TEXT NOT NULL REFERENCES tool_master(name) ON UPDATE CASCADE
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_events(
                  id BIGSERIAL PRIMARY KEY,
                  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
                  station_id TEXT NOT NULL DEFAULT 'pi1',
                  tag_uid TEXT NOT NULL,
                  role_hint TEXT CHECK (role_hint IN ('user','tool') OR role_hint IS NULL)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS loans(
                  id BIGSERIAL PRIMARY KEY,
                  tool_uid TEXT NOT NULL,
                  borrower_uid TEXT NOT NULL,
                  loaned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                  return_user_uid TEXT,
                  returned_at TIMESTAMPTZ
                )
                """
            )
    finally:
        conn.close()


def name_of_user(conn, uid: str) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT full_name FROM users WHERE uid=%s", (uid,))
        r = cur.fetchone()
    return r[0] if r else uid


def name_of_tool(conn, uid: str) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM tools WHERE uid=%s", (uid,))
        r = cur.fetchone()
    return r[0] if r else uid


def list_tool_names(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM tool_master ORDER BY name ASC")
        return [r[0] for r in cur.fetchall()]


def add_tool_name(conn, name: str) -> None:
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tool_master(name) VALUES(%s) ON CONFLICT(name) DO NOTHING",
            (name,),
        )


def delete_tool_name(conn, name: str) -> None:
    with conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM tools WHERE name=%s LIMIT 1", (name,))
        if cur.fetchone():
            raise RuntimeError(
                "この工具名は '工具' に割当済みです。先に tools 側を変更/削除してください。"
            )
        cur.execute("DELETE FROM tool_master WHERE name=%s", (name,))


def insert_scan(conn, uid: str, role: str | None = None) -> None:
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO scan_events(tag_uid, role_hint) VALUES (%s,%s)", (uid, role)
        )


def borrow_or_return(conn, user_uid: str, tool_uid: str):
    """貸出中なら返却、未貸出なら貸出を登録"""
    with conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, borrower_uid FROM loans
            WHERE tool_uid=%s AND returned_at IS NULL
            ORDER BY loaned_at DESC LIMIT 1
            """,
            (tool_uid,),
        )
        row = cur.fetchone()
        if row:  # 返却
            loan_id, prev_user = row
            cur.execute(
                """
                UPDATE loans
                   SET returned_at=NOW(), return_user_uid=%s
                 WHERE id=%s
                """,
                (user_uid, loan_id),
            )
            return "return", {"prev_user": prev_user}
        else:  # 新規貸出
            cur.execute(
                """
                INSERT INTO loans(tool_uid, borrower_uid) VALUES (%s,%s)
                """,
                (tool_uid, user_uid),
            )
            return "borrow", {}


def fetch_open_loans(conn, limit: int = 100):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(t.name, l.tool_uid) AS tool,
                   COALESCE(u.full_name, l.borrower_uid) AS borrower,
                   l.loaned_at
              FROM loans l
         LEFT JOIN tools t ON t.uid=l.tool_uid
         LEFT JOIN users u ON u.uid=l.borrower_uid
             WHERE l.returned_at IS NULL
          ORDER BY l.loaned_at DESC
             LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def fetch_recent_history(conn, limit: int = 50):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT CASE WHEN l.returned_at IS NULL THEN '貸出' ELSE '返却' END AS action,
                   COALESCE(t.name, l.tool_uid) AS tool,
                   COALESCE(u.full_name, l.borrower_uid) AS borrower,
                   l.loaned_at, l.returned_at
              FROM loans l
         LEFT JOIN tools t ON t.uid=l.tool_uid
         LEFT JOIN users u ON u.uid=l.borrower_uid
          ORDER BY COALESCE(l.returned_at, l.loaned_at) DESC
             LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()

