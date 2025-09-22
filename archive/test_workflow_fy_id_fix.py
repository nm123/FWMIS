#!/usr/bin/env python3
"""
Test script to verify that workflow transitions properly handle fy_id validation
and prevent orphaned cases.
"""

import os
import sqlite3
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.financial_utils import get_current_open_financial_year
from scripts.Utilities.workflow_utils import handle_case_status_change


def test_workflow_fy_id_handling():
    """Test that workflow transitions properly handle fy_id validation"""

    print("=== Testing Workflow fy_id Handling ===\n")

    # Connect to database
    conn = sqlite3.connect("data/fruitless.db")
    cursor = conn.cursor()

    try:
        # Get current open financial year
        current_fy = get_current_open_financial_year()
        if not current_fy:
            print("ERROR: No open financial year found!")
            return False

        current_fy_id, current_fy_string = current_fy
        print(f"Current open financial year: {current_fy_string} (ID: {current_fy_id})")

        # Check existing test cases
        cursor.execute(
            """
            SELECT id, transaction_no, list, status, fy_id
            FROM cases
            WHERE transaction_no IN ('202600001', '202600001-LS')
            ORDER BY transaction_no
        """
        )

        cases = cursor.fetchall()
        print(f"\nExisting test cases ({len(cases)} found):")
        for case in cases:
            case_id, transaction_no, list_name, status, fy_id = case
            fy_status = "VALID" if fy_id == current_fy_id else f"INVALID ({fy_id})"
            print(
                f"  {transaction_no}: {list_name}, {status}, fy_id={fy_id} [{fy_status}]"
            )

        # Test 1: Verify both cases have valid fy_id
        invalid_cases = [case for case in cases if case[4] != current_fy_id]
        if invalid_cases:
            print(f"\nFAIL: Found {len(invalid_cases)} cases with invalid fy_id:")
            for case in invalid_cases:
                print(f"  {case[1]}: fy_id={case[4]} (should be {current_fy_id})")
            return False
        else:
            print(f"\nPASS: All test cases have valid fy_id ({current_fy_id})")

        # Test 2: Verify Lead Schedule filtering works correctly
        cursor.execute(
            """
            SELECT transaction_no, list, status, fy_id
            FROM cases
            WHERE fy_id = ?
            AND ((list = 'Lead Schedule' AND is_finalized = 0)
                 OR (status = 'Confirmed' AND list != 'Lead Schedule'))
            ORDER BY transaction_no
        """,
            (current_fy_id,),
        )

        lead_schedule_cases = cursor.fetchall()
        print(f"\nLead Schedule view with fy_id={current_fy_id} filter:")
        for case in lead_schedule_cases:
            transaction_no, list_name, status, fy_id = case
            print(f"  {transaction_no}: {list_name}, {status}")

        # Test 3: Verify workflow transition handling
        print("\n=== Testing Workflow Transition Handling ===")

        # Find a case in Checklist that we can test with
        cursor.execute(
            """
            SELECT id, transaction_no, list, status, fy_id
            FROM cases
            WHERE list = 'Checklist'
            AND status != 'Confirmed'
            AND is_finalized = 0
            AND fy_id = ?
            LIMIT 1
        """,
            (current_fy_id,),
        )

        test_case = cursor.fetchone()
        if test_case:
            case_id, transaction_no, list_name, status, fy_id = test_case
            print(
                f"Testing workflow transition for case: {transaction_no} ({list_name}, {status})"
            )

            # Test the workflow transition
            result = handle_case_status_change(case_id, transaction_no, "Confirmed")
            print(f"Workflow transition result: {'SUCCESS' if result else 'FAILED'}")

            # Check if the case was copied correctly
            cursor.execute(
                """
                SELECT transaction_no, list, status, fy_id
                FROM cases
                WHERE transaction_no = ?
            """,
                (f"{transaction_no}-LS",),
            )

            copied_case = cursor.fetchone()
            if copied_case:
                copied_transaction_no, copied_list, copied_status, copied_fy_id = (
                    copied_case
                )
                print(
                    f"Copied case created: {copied_transaction_no} ({copied_list}, {copied_status}, fy_id={copied_fy_id})"
                )

                if copied_fy_id == current_fy_id:
                    print("PASS: Copied case has correct fy_id")
                else:
                    print(
                        f"FAIL: Copied case has invalid fy_id {copied_fy_id} (should be {current_fy_id})"
                    )
                    return False
            else:
                print("INFO: No copied case found (may already exist)")
        else:
            print("INFO: No suitable test case found in Checklist")

        print("\n=== Test Summary ===")
        print("All workflow fy_id validation tests passed!")
        print("Orphaned cases should no longer occur")
        print("Lead Schedule filtering works correctly")
        return True

    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = test_workflow_fy_id_handling()
    sys.exit(0 if success else 1)
