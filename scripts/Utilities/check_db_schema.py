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


def check_database_schema():
    """Check the database schema to identify missing columns"""

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("Checking database schema...")

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTables in database: {[t[0] for t in tables]}")

        # Check cases table schema
        print("\nCASES TABLE SCHEMA:")
        cursor.execute("PRAGMA table_info(cases)")
        columns = cursor.fetchall()

        print("Columns in cases table:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

        # Check if bas_journal_no column exists
        cursor.execute("PRAGMA table_info(cases)")
        column_names = [col[1] for col in cursor.fetchall()]

        required_columns = [
            "bas_journal_no",
            "bas_journal_date",
            "bas_payment_no",
            "bas_payment_date",
        ]

        print("\nCHECKING REQUIRED BAS COLUMNS:")
        for col in required_columns:
            if col in column_names:
                print(f"  + {col} - EXISTS")
            else:
                print(f"  - {col} - MISSING")

        # Show sample data from cases table
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        print(f"\nTotal cases in database: {case_count}")

        if case_count > 0:
            cursor.execute(
                """
                SELECT transaction_no, responsibility_id, bas_journal_no, bas_payment_no
                FROM cases
                ORDER BY transaction_no DESC
                LIMIT 3
            """
            )
            sample_cases = cursor.fetchall()

            print("\nSample case data:")
            for case in sample_cases:
                print(
                    f"  Case {case[0]}: RespID={case[1]}, Journal={case[2]}, Payment={case[3]}"
                )

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if "conn" in locals():
            conn.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    print("DATABASE SCHEMA CHECKER")
    print("=" * 50)
    check_database_schema()
