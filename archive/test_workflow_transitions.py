#!/usr/bin/env python3
"""
Test script to verify workflow transitions work correctly with fy_id validation.
"""

import os
import sqlite3
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.workflow_utils import handle_case_status_change


def test_workflow_transitions():
    """Test that workflow transitions work correctly with fy_id validation"""

    print("=== Testing Workflow Transitions with FY_ID Validation ===")
    print(f"Database path: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check current cases
        cursor.execute("SELECT COUNT(*) FROM cases WHERE list != 'Deleted Cases'")
        case_count = cursor.fetchone()[0]
        print(f"Current cases: {case_count}")

        # Find a case in Checklist with Alleged status
        cursor.execute(
            """
            SELECT id, transaction_no, list, status, fy_id
            FROM cases
            WHERE list = 'Checklist' AND status = 'Alleged' AND is_finalized = 0
            ORDER BY id DESC LIMIT 1
        """
        )
        test_case = cursor.fetchone()

        if test_case:
            case_id = test_case[0]
            transaction_no = test_case[1]
            current_list = test_case[2]
            current_status = test_case[3]
            current_fy_id = test_case[4]

            print(f"\nFound test case: {transaction_no} (ID: {case_id})")
            print(
                f"Current: List={current_list}, Status={current_status}, FY_ID={current_fy_id}"
            )

            # Test Confirmed status transition
            print("\n=== Testing Confirmed Status Transition ===")
            success = handle_case_status_change(
                case_id, transaction_no, "Confirmed", current_list
            )
            print(f"Workflow transition result: {success}")

            # Check the original case after transition (should be Confirmed in Checklist)
            cursor.execute(
                "SELECT list, status, fy_id FROM cases WHERE id = ?", (case_id,)
            )
            original_case = cursor.fetchone()
            print(
                f"Original case after transition: List={original_case[0]}, Status={original_case[1]}, FY_ID={original_case[2]}"
            )

            # Check if copy exists in Lead Schedule
            cursor.execute(
                "SELECT id, list, status, fy_id FROM cases WHERE transaction_no = ? AND list = 'Lead Schedule'",
                (f"{transaction_no}-LS",),
            )
            copied_case = cursor.fetchone()
            if copied_case:
                print(
                    f"Copied case in Lead Schedule: ID={copied_case[0]}, Transaction={transaction_no}-LS, List={copied_case[1]}, Status={copied_case[2]}, FY_ID={copied_case[3]}"
                )
                copy_exists = True
            else:
                print("ERROR: No copy found in Lead Schedule!")
                copy_exists = False

            # Verify fy_id is valid for both cases
            cursor.execute(
                "SELECT COUNT(*) FROM financial_years WHERE id = ?", (original_case[2],)
            )
            original_fy_exists = cursor.fetchone()[0]
            print(
                f"Original case FY_ID {original_case[2]} exists in financial_years: {original_fy_exists > 0}"
            )

            if copy_exists:
                cursor.execute(
                    "SELECT COUNT(*) FROM financial_years WHERE id = ?",
                    (copied_case[3],),
                )
                copy_fy_exists = cursor.fetchone()[0]
                print(
                    f"Copied case FY_ID {copied_case[3]} exists in financial_years: {copy_fy_exists > 0}"
                )

            # Reset cases for next test
            cursor.execute(
                "UPDATE cases SET list = ?, status = ?, is_finalized = 0 WHERE transaction_no = ?",
                ("Checklist", "Alleged", transaction_no),
            )
            cursor.execute(
                "DELETE FROM cases WHERE transaction_no = ?", (f"{transaction_no}-LS",)
            )
            conn.commit()
            print("Reset cases for next test")

            # Test Valid status transition
            print("\n=== Testing Valid Status Transition ===")
            success = handle_case_status_change(
                case_id, transaction_no, "Valid", current_list
            )
            print(f"Workflow transition result: {success}")

            # Check the case after transition
            cursor.execute(
                "SELECT list, status, fy_id, is_finalized FROM cases WHERE id = ?",
                (case_id,),
            )
            updated_case = cursor.fetchone()
            print(
                f"After Valid transition: List={updated_case[0]}, Status={updated_case[1]}, FY_ID={updated_case[2]}, Finalized={updated_case[3]}"
            )

            # Verify fy_id is valid
            cursor.execute(
                "SELECT COUNT(*) FROM financial_years WHERE id = ?", (updated_case[2],)
            )
            fy_exists = cursor.fetchone()[0]
            print(f"FY_ID {updated_case[2]} exists in financial_years: {fy_exists > 0}")

            # Check for orphaned cases
            print("\n=== Checking for Orphaned Cases ===")
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
            """
            )
            orphaned_count = cursor.fetchone()[0]
            print(f"Orphaned cases after transitions: {orphaned_count}")

            if orphaned_count > 0:
                print("Orphaned cases details:")
                cursor.execute(
                    """
                    SELECT id, transaction_no, list, status, fy_id
                    FROM cases
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
                    ORDER BY id DESC
                """
                )
                orphaned_cases = cursor.fetchall()
                for case in orphaned_cases:
                    print(
                        f"  ID: {case[0]}, Transaction: {case[1]}, List: {case[2]}, Status: {case[3]}, FY_ID: {case[4]}"
                    )

        else:
            print("No suitable test case found (Checklist with Alleged status)")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_workflow_transitions()
    if success:
        print("\n[SUCCESS] Workflow transitions test completed successfully!")
    else:
        print("\n[FAILED] Workflow transitions test failed!")
        sys.exit(1)
