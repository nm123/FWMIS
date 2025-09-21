#!/usr/bin/env python3
"""
Script to fix existing confirmed cases by moving them to Lead Schedule
"""

import sqlite3
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.workflow_utils import handle_case_status_change

def fix_existing_confirmed_cases():
    """Move existing confirmed cases to Lead Schedule"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== FIXING EXISTING CONFIRMED CASES ===")

    # Get all confirmed cases that are not already in Lead Schedule
    cursor.execute("""
        SELECT id, transaction_no, list, status
        FROM cases
        WHERE status = 'Confirmed' AND list != 'Lead Schedule'
    """)
    cases_to_fix = cursor.fetchall()

    print(f"Found {len(cases_to_fix)} confirmed cases to move to Lead Schedule:")

    fixed_count = 0
    for case_id, transaction_no, current_list, status in cases_to_fix:
        print(f"  Moving {transaction_no} from '{current_list}' to 'Lead Schedule'")

        # Use the workflow function to properly handle the transition
        success = handle_case_status_change(case_id, transaction_no, "Confirmed", "Lead Schedule")

        if success:
            fixed_count += 1
            print(f"    [SUCCESS] Moved {transaction_no}")
        else:
            print(f"    [FAILED] Could not move {transaction_no}")

    print(f"\nFixed {fixed_count} out of {len(cases_to_fix)} cases")

    # Verify the fix
    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Confirmed' AND list = 'Lead Schedule'")
    confirmed_in_lead = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Confirmed'")
    total_confirmed = cursor.fetchone()[0]

    print("\nVerification:")
    print(f"  Total confirmed cases: {total_confirmed}")
    print(f"  Confirmed cases in Lead Schedule: {confirmed_in_lead}")

    if confirmed_in_lead == total_confirmed:
        print("  [SUCCESS] All confirmed cases are now in Lead Schedule!")
    else:
        print(f"  [WARNING] {total_confirmed - confirmed_in_lead} confirmed cases are still not in Lead Schedule")

    conn.close()

if __name__ == "__main__":
    fix_existing_confirmed_cases()