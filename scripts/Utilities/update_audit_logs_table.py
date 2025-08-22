import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import BASE_DIR

def update_audit_logs_table():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Using database path: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if details column exists
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current audit_logs columns: {columns}")

        if 'details' not in columns:
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN details TEXT")
            conn.commit()
            print("Added 'details' column to audit_logs table.")
        else:
            print("'details' column already exists in audit_logs table.")

        # Verify table schema
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated audit_logs columns: {columns}")

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
    update_audit_logs_table()