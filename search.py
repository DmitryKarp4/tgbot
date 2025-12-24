import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "directory.db"

def search_people(query: str, limit: int = 10):
    q = (query or "").strip()
    if not q:
        return []

    q = q.lower()
    like = f"%{q}%"

    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("""
            SELECT fio, email, password, phone
            FROM people
            WHERE LOWER(fio) LIKE ?
               OR LOWER(email) LIKE ?
               OR LOWER(phone) LIKE ?
               OR LOWER(password) LIKE ?
            LIMIT ?
        """, (like, like, like, like, limit))
        return cur.fetchall()
