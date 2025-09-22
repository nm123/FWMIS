#!/usr/bin/env python3
"""
Script to move confirmed cases back to Checklist list
"""

import sqlite3

from scripts.Utilities.config import DB_PATH


def move_cases_back_to_checklist():
    """Move confirmed cases back to Checklist"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== MOVING CONFIRMED CASES BACK TO CHECKLIST ===")

    # Get all confirmed cases that are currently in Lead Schedule
    cursor.execute(
        """
        SELECT id, transaction_no, list, status
        FROM cases
        WHERE status = 'Confirmed' AND list = 'Lead Schedule'
    """
    )
    cases_to_move = cursor.fetchall()

    print(f"Found {len(cases_to_move)} confirmed cases in Lead Schedule to move back:")

    moved_count = 0
    for case_id, transaction_no, current_list, status in cases_to_move:
        print(f"  Moving {transaction_no} from '{current_list}' back to 'Checklist'")

        # Move case back to Checklist
        cursor.execute(
            """
            UPDATE cases
            SET list = 'Checklist'
            WHERE id = ?
        """,
            (case_id,),
        )

        moved_count += 1
        print(f"    [SUCCESS] Moved {transaction_no} back to Checklist")

    conn.commit()

    print(f"\nMoved {moved_count} out of {len(cases_to_move)} cases back to Checklist")

    # Verification
    cursor.execute(
        "SELECT COUNT(*) FROM cases WHERE status = 'Confirmed' AND list = 'Checklist'"
    )
    confirmed_in_checklist = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Confirmed'")
    total_confirmed = cursor.fetchone()[0]

    print("\nVerification:")
    print(f"  Total confirmed cases: {total_confirmed}")
    print(f"  Confirmed cases in Checklist: {confirmed_in_checklist}")

    if confirmed_in_checklist == total_confirmed:
        print("  [SUCCESS] All confirmed cases are back in Checklist!")
    else:
        print(
            f"  [WARNING] {total_confirmed - confirmed_in_checklist} confirmed cases are still not in Checklist"
        )

    conn.close()


if __name__ == "__main__":
    move_cases_back_to_checklist()
