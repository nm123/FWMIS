import sys
import os
import sqlite3
# Add parent directory (scripts) to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import BASE_DIR

def fix_email_templates_schema():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(email_templates)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current email_templates table columns: {columns}")

    if 'id' not in columns:
        # Create a new table with the correct schema
        cursor.execute("""
            CREATE TABLE email_templates_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        # Copy existing data
        cursor.execute("INSERT INTO email_templates_new (name) SELECT name FROM email_templates")
        # Drop old table and rename new one
        cursor.execute("DROP TABLE email_templates")
        cursor.execute("ALTER TABLE email_templates_new RENAME TO email_templates")
        conn.commit()
        print("Email templates table schema updated successfully.")
    else:
        print("Email templates table already has 'id' column.")

    # Verify the new schema
    cursor.execute("PRAGMA table_info(email_templates)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Updated email_templates table columns: {columns}")

    # List current email templates
    cursor.execute("SELECT id, name FROM email_templates")
    email_templates = cursor.fetchall()
    print(f"Email Templates ({len(email_templates)}): {email_templates}")

    conn.close()

if __name__ == "__main__":
    fix_email_templates_schema()