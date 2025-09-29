#!/usr/bin/env python3
"""
Clean up corrupted cases with NULL transaction_no values
"""

import sqlite3
from scripts.Utilities.config import DB_PATH

def clean_corrupted_cases():
    """Remove cases with NULL or empty transaction_no values"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM cases")
        total_before = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cases WHERE transaction_no IS NULL OR transaction_no = ''")
        corrupted_count = cursor.fetchone()[0]

        print(f"Total cases before cleanup: {total_before}")
        print(f"Corrupted cases (NULL/empty transaction_no): {corrupted_count}")

        if corrupted_count > 0:
            # Show some examples of corrupted cases
            cursor.execute("SELECT id, fy_id, amount FROM cases WHERE transaction_no IS NULL LIMIT 5")
            corrupted_samples = cursor.fetchall()
            print("Sample corrupted cases:")
            for case_id, fy_id, amount in corrupted_samples:
                print(f"  ID {case_id}: fy_id={fy_id}, amount={amount}")

            # Delete corrupted cases
            cursor.execute("DELETE FROM cases WHERE transaction_no IS NULL OR transaction_no = ''")
            deleted_count = cursor.rowcount
            conn.commit()

            print(f"Deleted {deleted_count} corrupted cases")

            # Check remaining cases
            cursor.execute("SELECT COUNT(*) FROM cases")
            total_after = cursor.fetchone()[0]
            print(f"Total cases after cleanup: {total_after}")

            # Show remaining valid cases
            cursor.execute("SELECT transaction_no FROM cases WHERE transaction_no IS NOT NULL LIMIT 10")
            valid_cases = cursor.fetchall()
            print("Remaining valid cases:")
            for (transaction_no,) in valid_cases:
                print(f"  {transaction_no}")

        else:
            print("No corrupted cases found")

    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    print("🧹 Cleaning up corrupted cases...")
    clean_corrupted_cases()
    print("✅ Cleanup complete!")
