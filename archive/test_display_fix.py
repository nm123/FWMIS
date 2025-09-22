#!/usr/bin/env python3
"""
Test script to verify that transaction number display stripping works correctly.
"""

import os
import sqlite3
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.config import DB_PATH


def test_display_stripping():
    """Test that transaction number suffixes are properly stripped for display"""

    print("=== Testing Transaction Number Display Stripping ===")
    print(f"Database path: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check current cases with suffixes
        cursor.execute(
            "SELECT transaction_no, list, status FROM cases WHERE transaction_no LIKE '%-LS' OR transaction_no LIKE '%-WOR' ORDER BY transaction_no"
        )
        suffixed_cases = cursor.fetchall()

        print(f"\nFound {len(suffixed_cases)} cases with suffixes:")
        for case in suffixed_cases:
            transaction_no, list_name, status = case
            # Simulate display stripping
            display_no = transaction_no
            if display_no.endswith("-LS") or display_no.endswith("-WOR"):
                display_no = display_no.rsplit("-", 1)[0]

            print(
                f"  DB: {transaction_no} -> Display: {display_no} (List: {list_name}, Status: {status})"
            )

        # Test the conversion logic
        print("\n=== Testing Display to Database Conversion ===")
        test_display_numbers = ["202600001", "202600002", "202600003"]

        for display_no in test_display_numbers:
            print(f"\nTesting display number: {display_no}")
            possible_case_nos = [display_no, f"{display_no}-LS", f"{display_no}-WOR"]

            for case_no in possible_case_nos:
                cursor.execute(
                    "SELECT id, list, status FROM cases WHERE transaction_no = ?",
                    (case_no,),
                )
                result = cursor.fetchone()
                if result:
                    case_id, list_name, status = result
                    print(
                        f"  Found: {case_no} -> ID: {case_id}, List: {list_name}, Status: {status}"
                    )
                    break
            else:
                print(f"  Not found: {display_no} (tried all variations)")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_display_stripping()
    if success:
        print("\n[SUCCESS] Display stripping test completed successfully!")
    else:
        print("\n[FAILED] Display stripping test failed!")
        sys.exit(1)
