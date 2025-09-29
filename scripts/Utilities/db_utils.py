import contextlib
import sqlite3
from typing import Iterator

from .config import DB_PATH

# Legacy compatibility - use database_connection.py instead
from .database_connection import db_transaction, get_db_connection


def get_current_delegation():
    """Get the current CFO delegation limit (most recent by effective date)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT cfo_limit, effective_date 
                FROM write_off_delegations 
                ORDER BY effective_date DESC 
                LIMIT 1
            """
            )
            row = cursor.fetchone()
            return {"cfo_limit": row[0], "effective_date": row[1]} if row else None
    except sqlite3.Error as e:
        import logging

        logging.error(f"Database error getting current delegation: {e}")
        return None


def save_delegation(cfo_limit, effective_date):
    """Save a new delegation limit."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO write_off_delegations (cfo_limit, effective_date)
                VALUES (?, ?)
            """,
                (cfo_limit, effective_date),
            )
            return True
    except sqlite3.Error as e:
        import logging

        logging.error(f"Error saving delegation: {e}")
        return False
