import logging
import sqlite3

log = logging.getLogger(__name__)


def get_orders(conn: sqlite3.Connection, customer_id: int, status: str | None = None) -> list[tuple]:
    sql = "SELECT id, total, status FROM orders WHERE customer_id = ?"
    params: list[object] = [customer_id]
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    return conn.execute(sql, params).fetchall()


def safe_import(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    try:
        with conn:
            conn.executemany("INSERT INTO orders (id, total, status) VALUES (?, ?, ?)", rows)
    except Exception:
        log.exception("Import of %d rows failed", len(rows))
        raise
