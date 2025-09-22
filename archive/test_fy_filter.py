#!/usr/bin/env python3
"""
Test script to verify financial year filtering functionality
"""

import sqlite3

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (get_all_financial_years,
                                               get_current_open_financial_year)


def test_fy_filter():
    """Test financial year filtering functionality"""

    print("=== FINANCIAL YEAR FILTER TEST ===")

    # Test getting all financial years
    financial_years = get_all_financial_years()
    print(f"\nAvailable financial years ({len(financial_years)} total):")
    for fy_id, fy_string, is_open in financial_years:
        status = "[OPEN]" if is_open else "[CLOSED]"
        print(f"  {fy_string} (ID: {fy_id}) {status}")

    # Test getting current open financial year
    current_open = get_current_open_financial_year()
    if current_open:
        fy_id, fy_string = current_open
        print(f"\nCurrent open financial year: {fy_string} (ID: {fy_id})")
    else:
        print("\nNo current open financial year found")

    # Test database filtering
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if current_open:
        fy_id, fy_string = current_open

        # Count cases in current financial year
        cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ?", (fy_id,))
        current_fy_count = cursor.fetchone()[0]

        print(f"\nCases in current financial year ({fy_string}): {current_fy_count}")

        # Show sample cases
        cursor.execute(
            """
            SELECT transaction_no, list, status
            FROM cases
            WHERE fy_id = ?
            LIMIT 5
        """,
            (fy_id,),
        )

        sample_cases = cursor.fetchall()
        if sample_cases:
            print("Sample cases:")
            for case_no, list_name, status in sample_cases:
                print(f"  {case_no}: {list_name} - {status}")

    # Count total cases
    cursor.execute("SELECT COUNT(*) FROM cases WHERE list != 'Deleted Cases'")
    total_cases = cursor.fetchone()[0]
    print(f"\nTotal active cases: {total_cases}")

    conn.close()

    print("\n=== TEST COMPLETE ===")


if __name__ == "__main__":
    test_fy_filter()
