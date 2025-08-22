import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import BASE_DIR

def create_contacts_table():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Using database path: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                responsibility_id INTEGER,
                name TEXT NOT NULL,
                email TEXT,
                FOREIGN KEY (responsibility_id) REFERENCES responsibilities (id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("Contacts table created successfully.")

        # Verify table
        cursor.execute("PRAGMA table_info(contacts)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Contacts table columns: {columns}")

        # Verify database contents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")

        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    create_contacts_table()