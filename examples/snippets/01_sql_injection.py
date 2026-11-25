import sqlite3


def find_user(db_path: str, username: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    try:
        query = "SELECT id, username, email FROM users WHERE username = '" + username + "'"
        row = conn.execute(query).fetchone()
        if row is None:
            return None
        return {"id": row[0], "username": row[1], "email": row[2]}
    finally:
        conn.close()
