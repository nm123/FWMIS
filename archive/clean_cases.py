import sqlite3
import os
import sys

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(scripts_dir)

try:
    from scripts.Utilities.config import DB_PATH
except ImportError:
    # Fallback if config.py is missing
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DB_PATH = os.path.join(DATA_DIR, 'fruitless.db')
    print(f"Warning: config.py not found, using fallback paths")

def clean_all_cases():
    """Delete all cases from the database while keeping other data intact"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get count of cases before deletion
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        print(f"Found {case_count} cases in database")

        # Delete all cases
        cursor.execute("DELETE FROM cases")
        conn.commit()

        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM cases")
        remaining_count = cursor.fetchone()[0]
        print(f"Deleted {case_count} cases. {remaining_count} cases remaining.")

        # Check that other tables are intact
        cursor.execute("SELECT COUNT(*) FROM responsibilities")
        resp_count = cursor.fetchone()[0]
        print(f"Responsibilities table: {resp_count} records (should be intact)")

        cursor.execute("SELECT COUNT(*) FROM categories")
        cat_count = cursor.fetchone()[0]
        print(f"Categories table: {cat_count} records (should be intact)")

        cursor.execute("SELECT COUNT(*) FROM email_templates")
        email_count = cursor.fetchone()[0]
        print(f"Email templates table: {email_count} records (should be intact)")

        conn.close()
        print("Database cleanup completed successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting database cleanup - deleting all cases...")
    clean_all_cases()