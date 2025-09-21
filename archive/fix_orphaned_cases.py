#!/usr/bin/env python3
"""
Script to fix orphaned cases with invalid fy_id values
"""

import sqlite3
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_current_open_financial_year

def main():
    print("Fixing orphaned cases with invalid fy_id values...")

    # Get current open financial year
    current_fy = get_current_open_financial_year()
    if not current_fy:
        print("ERROR: No open financial year found!")
        return

    fy_id, fy_string = current_fy
    print(f"Current open FY: {fy_string} (ID: {fy_id})")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Find all fy_id values that don't exist in financial_years table
        cursor.execute("""
            SELECT DISTINCT c.fy_id, COUNT(*) as case_count
            FROM cases c
            LEFT JOIN financial_years fy ON c.fy_id = fy.id
            WHERE c.list != 'Deleted Cases'
              AND fy.id IS NULL
              AND c.fy_id IS NOT NULL
            GROUP BY c.fy_id
        """)

        orphaned_fy_ids = cursor.fetchall()
        print(f"Found {len(orphaned_fy_ids)} orphaned fy_id values:")

        total_fixed = 0
        for orphaned_fy_id, case_count in orphaned_fy_ids:
            print(f"  fy_id {orphaned_fy_id}: {case_count} cases")

            # Update cases with this orphaned fy_id
            cursor.execute(
                "UPDATE cases SET fy_id = ? WHERE fy_id = ? AND list != 'Deleted Cases'",
                (fy_id, orphaned_fy_id)
            )
            updated = cursor.rowcount
            total_fixed += updated
            print(f"    Updated {updated} cases")

        conn.commit()
        print(f"\nTotal cases fixed: {total_fixed}")

        # Verify the fix
        cursor.execute("""
            SELECT COUNT(*) FROM cases c
            LEFT JOIN financial_years fy ON c.fy_id = fy.id
            WHERE c.list != 'Deleted Cases' AND fy.id IS NULL
        """)
        remaining_orphaned = cursor.fetchone()[0]
        print(f"Remaining orphaned cases: {remaining_orphaned}")

        if remaining_orphaned == 0:
            print("✅ All orphaned cases have been fixed!")
        else:
            print("⚠️  Some orphaned cases remain")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()