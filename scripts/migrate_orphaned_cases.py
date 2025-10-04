import sqlite3
import shutil
import os
from pathlib import Path

DB_PATH = Path("data/fruitless.db")
BACKUP_PATH = Path("data/fruitless_backup.db")

def main():
    # Backup the database
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"Database backed up to {BACKUP_PATH}")
    else:
        print(f"Database not found at {DB_PATH}")
        return

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Find current open FY ID
        cursor.execute("SELECT id FROM financial_years WHERE status = 'open' LIMIT 1")
        result = cursor.fetchone()
        if not result:
            print("No open financial year found.")
            return
        current_fy_id = result[0]
        print(f"Current open FY ID: {current_fy_id}")

        # Check for cases in FY 149 that are not deleted
        cursor.execute(
            "SELECT COUNT(*) FROM cases WHERE fy_id = ? AND list != 'Deleted Cases'",
            (149,)
        )
        count = cursor.fetchone()[0]
        print(f"Found {count} cases in FY 149 (non-deleted) to migrate.")

        if count == 0:
            print("No cases to migrate.")
            return

        # Perform the migration: update fy_id to current, set period_id to NULL
        cursor.execute(
            """
            UPDATE cases
            SET fy_id = ?, period_id = NULL
            WHERE fy_id = ? AND list != 'Deleted Cases'
            """,
            (current_fy_id, 149)
        )
        migrated = cursor.rowcount
        conn.commit()

        print(f"Migrated {migrated} cases from FY 149 to FY {current_fy_id}.")
        print("Migration completed successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()