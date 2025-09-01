import sqlite3
import os

# Get the database path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(BASE_DIR, 'data', 'fruitless.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Add subject column to email_templates if it doesn't exist
    cursor.execute("PRAGMA table_info(email_templates)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'subject' not in columns:
        cursor.execute("ALTER TABLE email_templates ADD COLUMN subject TEXT")
        print("Added subject column to email_templates")
    else:
        print("Subject column already exists in email_templates")

    # Create lists table if it doesn't exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lists'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE lists (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                is_default INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0
            )
        """)
        print("Created lists table")
    else:
        print("Lists table already exists")

    conn.commit()
    print("Database schema fixed successfully")

except sqlite3.Error as e:
    print(f"Database error: {e}")
    conn.rollback()

finally:
    conn.close()