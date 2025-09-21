#!/usr/bin/env python3
"""
Test script to verify the workflow fix for Confirmed cases moving to Lead Schedule
"""

import sqlite3
from scripts.Utilities.config import DB_PATH

def test_workflow_fix():
    """Test that confirmed cases are properly moved to Lead Schedule"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== WORKFLOW FIX TEST ===")

    # Check cases with Confirmed status
    cursor.execute("SELECT transaction_no, list, status, is_finalized FROM cases WHERE status = 'Confirmed'")
    confirmed_cases = cursor.fetchall()

    print(f"\nCases with Confirmed status ({len(confirmed_cases)} total):")
    for case in confirmed_cases:
        transaction_no, list_name, status, is_finalized = case
        print(f"  {transaction_no}: List='{list_name}', Status='{status}', Finalized={is_finalized}")

    # Check cases that would appear in Lead Schedule (list = 'Lead Schedule' OR status = 'Confirmed')
    cursor.execute("SELECT transaction_no, list, status, is_finalized FROM cases WHERE (list = 'Lead Schedule' AND is_finalized = 0) OR status = 'Confirmed'")
    lead_schedule_cases = cursor.fetchall()

    print(f"\nCases that would appear in Lead Schedule ({len(lead_schedule_cases)} total):")
    for case in lead_schedule_cases:
        transaction_no, list_name, status, is_finalized = case
        print(f"  {transaction_no}: List='{list_name}', Status='{status}', Finalized={is_finalized}")

    # Check for confirmed cases NOT in Lead Schedule (potential issue)
    cursor.execute("""
        SELECT transaction_no, list, status, is_finalized
        FROM cases
        WHERE status = 'Confirmed' AND list != 'Lead Schedule'
    """)
    misplaced_cases = cursor.fetchall()

    if misplaced_cases:
        print(f"\n[WARNING] Confirmed cases NOT in Lead Schedule ({len(misplaced_cases)} total):")
        for case in misplaced_cases:
            transaction_no, list_name, status, is_finalized = case
            print(f"  {transaction_no}: List='{list_name}', Status='{status}', Finalized={is_finalized}")
    else:
        print("\n[SUCCESS] All confirmed cases are in Lead Schedule!")

    # Check for cases in Lead Schedule that are finalized (shouldn't show in filter)
    cursor.execute("""
        SELECT transaction_no, list, status, is_finalized
        FROM cases
        WHERE list = 'Lead Schedule' AND is_finalized = 1
    """)
    finalized_lead_cases = cursor.fetchall()

    if finalized_lead_cases:
        print(f"\n[INFO] Finalized cases in Lead Schedule ({len(finalized_lead_cases)} total) - these won't show in Lead Schedule filter:")
        for case in finalized_lead_cases:
            transaction_no, list_name, status, is_finalized = case
            print(f"  {transaction_no}: List='{list_name}', Status='{status}', Finalized={is_finalized}")

    conn.close()

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_workflow_fix()