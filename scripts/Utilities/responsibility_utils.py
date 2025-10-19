from .config import DB_PATH, logging


def load_responsibilities():
    import sqlite3

    try:
        print(f"Connecting to database: {DB_PATH}")  # Debug line
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='responsibilities'"
        )
        if not cursor.fetchone():
            print("Table 'responsibilities' not found in database")
        cursor.execute(
            "SELECT id, name, parent_id, is_posting_level FROM responsibilities"
        )
        responsibilities = [
            {
                "id": row[0],
                "name": row[1],
                "parent_id": row[2],
                "is_posting_level": row[3],
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return responsibilities
    except sqlite3.Error as e:
        logging.error(f"Failed to load responsibilities: {e}")
        print(f"Database error: {e}")  # Debug line
        return []


def load_posting_responsibilities():
    """Load only posting level responsibilities for case creation"""
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            (
                "SELECT id, name, parent_id, is_posting_level "
                "FROM responsibilities "
                "WHERE is_posting_level = 1"
            )
        )
        responsibilities = [
            {
                "id": row[0],
                "name": row[1],
                "parent_id": row[2],
                "is_posting_level": row[3],
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return responsibilities
    except sqlite3.Error as e:
        logging.error(f"Failed to load posting responsibilities: {e}")
        return []
