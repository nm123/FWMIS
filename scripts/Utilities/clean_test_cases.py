import sqlite3
import os
import sys

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import DB_PATH

def clean_test_cases():
    """Clean up test cases from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Count cases before cleanup
        cursor.execute("SELECT COUNT(*) FROM cases")
        count_before = cursor.fetchone()[0]
        print(f"Cases before cleanup: {count_before}")

        # Delete all cases (since they appear to be test cases)
        cursor.execute("DELETE FROM cases")
        deleted_count = cursor.rowcount

        # Reset the case counter for the current financial year
        cursor.execute("DELETE FROM fy_case_counters")

        conn.commit()
        conn.close()

        print(f"Deleted {deleted_count} test cases")
        print("Reset case counter to start from 001")
        print("You can now create your first case with number 202600001")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    print("=== DATABASE CLEANUP ===")
    print("WARNING: This will permanently delete ALL cases from the database!")
    print("Make sure to backup any important data before proceeding.")
    print()

    # Uncomment the next line to actually perform the cleanup:
    # clean_test_cases()

    print("Currently showing PREVIEW only (no changes made)")
    print("To actually clean up:")
    print("1. Uncomment the line: clean_test_cases()")
    print("2. Save the file")
    print("3. Run: python scripts/Utilities/clean_test_cases.py")
    print()

    # Preview what would be deleted
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cases")
        count = cursor.fetchone()[0]
        print(f"Cases that would be deleted: {count}")

        if count > 0:
            cursor.execute("SELECT transaction_no FROM cases LIMIT 3")
            samples = cursor.fetchall()
            print("Sample case numbers:", [row[0] for row in samples])
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")