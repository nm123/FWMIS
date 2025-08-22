import sqlite3
import os
from pathlib import Path

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
db_path = os.path.join(BASE_DIR, "fruitless.db")

def fix_categories_schema():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(categories)")
    columns = [info[1] for info in cursor.fetchall()]
    print("Current categories table columns:", columns)

    # Create new table with correct schema
    cursor.execute("DROP TABLE IF EXISTS categories_new")
    cursor.execute("""
        CREATE TABLE categories_new (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)

    # Migrate existing data
    cursor.execute("SELECT name FROM categories")
    categories = cursor.fetchall()
    for i, (name,) in enumerate(categories, 1):
        cursor.execute("INSERT INTO categories_new (id, name) VALUES (?, ?)", (i, name))

    # Drop old table and rename new table
    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute("ALTER TABLE categories_new RENAME TO categories")
    conn.commit()
    conn.close()
    print("Categories table schema updated successfully")

if __name__ == "__main__":
    fix_categories_schema()