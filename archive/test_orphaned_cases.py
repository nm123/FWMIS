#!/usr/bin/env python3
"""
Test script to reproduce and debug orphaned cases issue.
Run this script to see debug output when creating and editing cases.
"""

import os
import sqlite3
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.workflow_utils import handle_case_status_change


def test_case_creation_and_editing():
    """Test creating a case and then editing it to trigger workflow transitions"""

    print("=== Testing Orphaned Cases Issue ===")
    print(f"Database path: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check current financial years
        print("\n=== Current Financial Years ===")
        cursor.execute(
            "SELECT id, start_year, end_year, status FROM financial_years ORDER BY id"
        )
        fy_results = cursor.fetchall()
        for fy in fy_results:
            print(f"ID: {fy[0]}, Year: {fy[1]}-{fy[2]}, Status: {fy[3]}")

        # Check current cases
        print("\n=== Current Cases (first 10) ===")
        cursor.execute(
            """
            SELECT id, transaction_no, list, status, fy_id
            FROM cases
            WHERE list != 'Deleted Cases'
            ORDER BY id DESC LIMIT 10
        """
        )
        case_results = cursor.fetchall()
        for case in case_results:
            print(
                f"ID: {case[0]}, Transaction: {case[1]}, List: {case[2]}, Status: {case[3]}, FY_ID: {case[4]}"
            )

        # Check for orphaned cases
        print("\n=== Checking for Orphaned Cases ===")
        cursor.execute(
            """
            SELECT COUNT(*) FROM cases c
            LEFT JOIN financial_years fy ON c.fy_id = fy.id
            WHERE fy.id IS NULL AND c.list != 'Deleted Cases'
        """
        )
        orphaned_count = cursor.fetchone()[0]
        print(f"Current orphaned cases: {orphaned_count}")

        if orphaned_count > 0:
            print("\nOrphaned cases details:")
            cursor.execute(
                """
                SELECT c.id, c.transaction_no, c.list, c.status, c.fy_id
                FROM cases c
                LEFT JOIN financial_years fy ON c.fy_id = fy.id
                WHERE fy.id IS NULL AND c.list != 'Deleted Cases'
                ORDER BY c.id DESC
            """
            )
            orphaned_cases = cursor.fetchall()
            for case in orphaned_cases:
                print(
                    f"  ID: {case[0]}, Transaction: {case[1]}, List: {case[2]}, Status: {case[3]}, FY_ID: {case[4]}"
                )

        # Test workflow transition manually
        print("\n=== Testing Workflow Transition ===")

        # Find a case that's still in Checklist with Alleged status
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

            print(
                f"Testing workflow transition for case {transaction_no} (ID: {case_id})"
            )
            print(f"Current: List={current_list}, Status={current_status}")

            # Test Valid status transition
            print("Attempting to change status to Valid...")
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

            # Reset for next test
            cursor.execute(
                "UPDATE cases SET status = ?, is_finalized = 0 WHERE id = ?",
                ("Alleged", case_id),
            )
            conn.commit()
            print("Reset case for next test")

            # Test Confirmed status transition
            print("Attempting to change status to Confirmed...")
            success = handle_case_status_change(
                case_id, transaction_no, "Confirmed", current_list
            )
            print(f"Workflow transition result: {success}")

            # Check the case after transition
            cursor.execute(
                "SELECT list, status, fy_id FROM cases WHERE id = ?", (case_id,)
            )
            updated_case = cursor.fetchone()
            print(
                f"After Confirmed transition: List={updated_case[0]}, Status={updated_case[1]}, FY_ID={updated_case[2]}"
            )
        else:
            print("No suitable test case found (Checklist with Alleged status)")

        conn.close()

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_case_creation_and_editing()
