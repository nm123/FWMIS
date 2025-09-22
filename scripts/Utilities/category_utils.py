from .config import DB_PATH, logging


def load_categories():
    import sqlite3

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Alter table to add compulsory columns if not exist
        cursor.execute("PRAGMA table_info(categories)")
        columns = [col[1] for col in cursor.fetchall()]
        if "persal_compulsory" not in columns:
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN persal_compulsory INTEGER DEFAULT 0"
            )
        if "bas_payment_compulsory" not in columns:
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN bas_payment_compulsory INTEGER DEFAULT 0"
            )
        conn.commit()
        cursor.execute(
            "SELECT id, name, parent_id, persal_compulsory, bas_payment_compulsory FROM categories"
        )
        categories = [
            {
                "id": row[0],
                "name": row[1],
                "parent_id": row[2],
                "persal_compulsory": bool(row[3]),
                "bas_payment_compulsory": bool(row[4]),
            }
            for row in cursor.fetchall()
        ]
        return categories
    except sqlite3.Error as e:
        logging.error(f"Failed to load categories: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading categories: {e}")
        return []
    finally:
        if conn:
            conn.close()


def save_categories(categories):
    import sqlite3

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories")
        for category in categories:
            cursor.execute(
                "INSERT INTO categories (id, name, parent_id, persal_compulsory, bas_payment_compulsory) VALUES (?, ?, ?, ?, ?)",
                (
                    category["id"],
                    category["name"],
                    category["parent_id"],
                    1 if category.get("persal_compulsory", False) else 0,
                    1 if category.get("bas_payment_compulsory", False) else 0,
                ),
            )
        conn.commit()
        logging.info(f"Successfully saved {len(categories)} categories")
    except sqlite3.Error as e:
        logging.error(f"Failed to save categories: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logging.error(f"Unexpected error saving categories: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
