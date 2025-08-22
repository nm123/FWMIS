import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import BASE_DIR

def update_contacts_table():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Using database path: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current columns
        cursor.execute("PRAGMA table_info(contacts)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current contacts columns: {columns}")

        # Add title column if not exists
        if 'title' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN title TEXT")
            print("Added 'title' column to contacts table.")

        # Add telephone column if not exists
        if 'telephone' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN telephone TEXT")
            print("Added 'telephone' column to contacts table.")

        conn.commit()

        # Verify updated schema
        cursor.execute("PRAGMA table_info(contacts)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated contacts columns: {columns}")

        # Verify database tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")

        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    update_contacts_table()