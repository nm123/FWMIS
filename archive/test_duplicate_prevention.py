#!/usr/bin/env python3
"""
Test script to verify that duplicate cases are prevented in Lead Schedule view.
"""

import os
import sqlite3
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.config import DB_PATH


def test_duplicate_prevention():
    """Test that Lead Schedule view doesn't show duplicate cases"""

    print("=== Testing Duplicate Prevention in Lead Schedule View ===")
    print(f"Database path: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check current cases
        cursor.execute("SELECT COUNT(*) FROM cases WHERE list != 'Deleted Cases'")
        case_count = cursor.fetchone()[0]
        print(f"Total cases: {case_count}")

        # Check cases in Lead Schedule
        cursor.execute("SELECT COUNT(*) FROM cases WHERE list = 'Lead Schedule'")
        lead_schedule_count = cursor.fetchone()[0]
        print(f"Cases in Lead Schedule list: {lead_schedule_count}")

        # Check cases with Confirmed status
        cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Confirmed'")
        confirmed_count = cursor.fetchone()[0]
        print(f"Cases with Confirmed status: {confirmed_count}")

        # Test the Lead Schedule query logic
        print("\n=== Testing Lead Schedule Query Logic ===")

        # Query that simulates the Lead Schedule view
        cursor.execute(
            """
            SELECT transaction_no, list, status
            FROM cases
            WHERE fy_id = 7 AND (
                (list = 'Lead Schedule' AND is_finalized = 0)
                OR (status = 'Confirmed' AND list != 'Lead Schedule')
            )
            ORDER BY transaction_no
        """
        )

        lead_schedule_results = cursor.fetchall()
        print(f"Lead Schedule view results: {len(lead_schedule_results)} cases")

        # Check for duplicates
        transaction_nos = [row[0] for row in lead_schedule_results]
        unique_transaction_nos = set()

        duplicates_found = []
        for i, txn_no in enumerate(transaction_nos):
            # Strip suffixes for comparison
            base_txn_no = (
                txn_no.rsplit("-", 1)[0] if txn_no.endswith(("-LS", "-WOR")) else txn_no
            )

            if base_txn_no in unique_transaction_nos:
                duplicates_found.append((i, txn_no, base_txn_no))
            else:
                unique_transaction_nos.add(base_txn_no)

        if duplicates_found:
            print(f"[ERROR] Found {len(duplicates_found)} duplicate cases:")
            for dup in duplicates_found:
                print(f"  Row {dup[0]}: {dup[1]} (base: {dup[2]})")
        else:
            print("[OK] No duplicate cases found in Lead Schedule view")

        # Show sample results
        print("\n=== Sample Lead Schedule Results ===")
        for i, row in enumerate(lead_schedule_results[:5]):  # Show first 5
            txn_no, list_name, status = row
            base_txn_no = (
                txn_no.rsplit("-", 1)[0] if txn_no.endswith(("-LS", "-WOR")) else txn_no
            )
            print(
                f"  {i+1}. Display: {base_txn_no}, DB: {txn_no}, List: {list_name}, Status: {status}"
            )

        if len(lead_schedule_results) > 5:
            print(f"  ... and {len(lead_schedule_results) - 5} more cases")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False

    return len(duplicates_found) == 0


if __name__ == "__main__":
    success = test_duplicate_prevention()
    if success:
        print("\n[SUCCESS] Duplicate prevention test passed!")
    else:
        print("\n[FAILED] Duplicate prevention test failed!")
        sys.exit(1)
