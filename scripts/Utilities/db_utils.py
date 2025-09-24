import sqlite3
from typing import Iterator
import contextlib

from .config import DB_PATH


@contextlib.contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with recommended PRAGMAs enabled.

    Ensures foreign key enforcement and WAL journaling for better reliability.
    Commits on normal exit and rolls back on exception.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        # Enforce constraints and improve concurrency
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_current_delegation():
    """Get the current CFO delegation limit (most recent by effective date)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cfo_limit, effective_date 
                FROM write_off_delegations 
                ORDER BY effective_date DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return {'cfo_limit': row[0], 'effective_date': row[1]} if row else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def save_delegation(cfo_limit, effective_date):
    """Save a new delegation limit."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO write_off_delegations (cfo_limit, effective_date)
                VALUES (?, ?)
            """, (cfo_limit, effective_date))
            return True
    except sqlite3.Error as e:
        print(f"Error saving delegation: {e}")
        return False