import os
import sqlite3
import sys

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(scripts_dir)

try:
    from config import DB_PATH
except ImportError:
    # Fallback if config.py is missing
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )
    DB_PATH = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Warning: config.py not found, using fallback paths")
except Exception as e:
    print(f"Error loading config: {e}")
    sys.exit(1)


def add_missing_columns():
    """Add missing BAS journal columns to the cases table"""

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("Adding missing BAS journal columns to cases table...")

        # Check current schema
        cursor.execute("PRAGMA table_info(cases)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Add bas_journal_no column if it doesn't exist
        if "bas_journal_no" not in column_names:
            print("Adding bas_journal_no column...")
            cursor.execute("ALTER TABLE cases ADD COLUMN bas_journal_no TEXT")
        else:
            print("bas_journal_no column already exists")

        # Add bas_journal_date column if it doesn't exist
        if "bas_journal_date" not in column_names:
            print("Adding bas_journal_date column...")
            cursor.execute("ALTER TABLE cases ADD COLUMN bas_journal_date TEXT")
        else:
            print("bas_journal_date column already exists")

        # Commit the changes
        conn.commit()

        # Verify the changes
        cursor.execute("PRAGMA table_info(cases)")
        updated_columns = cursor.fetchall()
        updated_column_names = [col[1] for col in updated_columns]

        print("\nUpdated cases table columns:")
        for col in updated_columns:
            print(f"  - {col[1]} ({col[2]})")

        print("\nChecking required BAS columns:")
        required_columns = [
            "bas_journal_no",
            "bas_journal_date",
            "bas_payment_no",
            "bas_payment_date",
        ]
        for col in required_columns:
            if col in updated_column_names:
                print(f"  + {col} - EXISTS")
            else:
                print(f"  - {col} - MISSING")

        conn.close()
        print("\nDatabase schema updated successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if "conn" in locals():
            conn.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    print("DATABASE SCHEMA UPDATE")
    print("=" * 50)
    add_missing_columns()
