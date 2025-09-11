#!/usr/bin/env python3
"""
Test script to verify the suffix-based filtering logic for case management system.
"""

import sqlite3
import os

# Get database path (same as used by the application)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'fruitless.db')

def test_filtering_logic():
    """Test the new suffix-based filtering logic"""

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("=== TESTING SUFFIX-BASED FILTERING LOGIC ===\n")

        # Test Checklist filtering (should show only cases without -LS or -WOR suffixes)
        print("1. CHECKLIST FILTER (cases without -LS or -WOR suffixes):")
        cursor.execute("""
            SELECT transaction_no, list, status
            FROM cases
            WHERE list != 'Deleted Cases'
            AND transaction_no NOT LIKE '%-LS'
            AND transaction_no NOT LIKE '%-WOR'
            ORDER BY transaction_no
        """)
        checklist_cases = cursor.fetchall()
        for case_no, list_name, status in checklist_cases:
            print(f"  {case_no} - {list_name} - {status}")
        print(f"  Total: {len(checklist_cases)} cases\n")

        # Test Lead Schedule filtering (should show cases with -LS)
        print("2. LEAD SCHEDULE FILTER (cases with -LS suffix):")
        cursor.execute("""
            SELECT transaction_no, list, status
            FROM cases
            WHERE list != 'Deleted Cases'
            AND transaction_no LIKE '%-LS'
            ORDER BY transaction_no
        """)
        lead_schedule_cases = cursor.fetchall()
        for case_no, list_name, status in lead_schedule_cases:
            print(f"  {case_no} - {list_name} - {status}")
        print(f"  Total: {len(lead_schedule_cases)} cases\n")

        # Test Write-Off Recommended filtering (should show cases with -WOR)
        print("3. WRITE-OFF RECOMMENDED FILTER (cases with -WOR suffix):")
        cursor.execute("""
            SELECT transaction_no, list, status
            FROM cases
            WHERE list != 'Deleted Cases'
            AND transaction_no LIKE '%-WOR'
            ORDER BY transaction_no
        """)
        wor_cases = cursor.fetchall()
        for case_no, list_name, status in wor_cases:
            print(f"  {case_no} - {list_name} - {status}")
        print(f"  Total: {len(wor_cases)} cases\n")

        # Show all cases with their current suffixes
        print("4. ALL CASES WITH SUFFIX STATUS:")
        cursor.execute("""
            SELECT transaction_no, list, status,
                   CASE
                       WHEN transaction_no LIKE '%-LS' THEN 'Has -LS'
                       WHEN transaction_no LIKE '%-WOR' THEN 'Has -WOR'
                       ELSE 'No suffix'
                   END as suffix_status
            FROM cases
            WHERE list != 'Deleted Cases'
            ORDER BY transaction_no
        """)
        all_cases = cursor.fetchall()
        for case_no, list_name, status, suffix_status in all_cases:
            print(f"  {case_no} - {list_name} - {status} - {suffix_status}")
        print(f"  Total: {len(all_cases)} cases\n")

        # Test display logic (stripping suffixes)
        print("5. DISPLAY LOGIC TEST (stripping suffixes for UI):")
        for case_no, list_name, status, suffix_status in all_cases:
            # Simulate the display logic from view_cases.py
            display_value = case_no
            if display_value.endswith('-LS') or display_value.endswith('-WOR'):
                display_value = display_value.rsplit('-', 1)[0]
            print(f"  DB: {case_no} -> Display: {display_value}")

        conn.close()

        print("\n=== FILTERING LOGIC TEST COMPLETED ===")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals():
            conn.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_filtering_logic()