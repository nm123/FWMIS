#!/usr/bin/env python3
"""
Script to check fy_id values and fix cases that don't have fy_id set
"""

import sqlite3
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_current_open_financial_year

def check_and_fix_fy_ids():
    """Check fy_id values and assign current FY to cases without fy_id"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== CHECKING AND FIXING FY_ID VALUES ===")

    # Check fy_id values for cases
    cursor.execute('SELECT fy_id, COUNT(*) FROM cases GROUP BY fy_id')
    fy_counts = cursor.fetchall()

    print('Financial year distribution of cases:')
    for fy_id, count in fy_counts:
        if fy_id is not None:
            print(f'  FY ID {fy_id}: {count} cases')
        else:
            print(f'  NULL fy_id: {count} cases')

    # Check if cases have fy_id set
    cursor.execute('SELECT COUNT(*) FROM cases WHERE fy_id IS NULL')
    null_count = cursor.fetchone()[0]
    print(f'\nCases with NULL fy_id: {null_count}')

    # Get current open financial year
    current_open = get_current_open_financial_year()
    if current_open:
        fy_id, fy_string = current_open
        print(f'\nCurrent open financial year: {fy_string} (ID: {fy_id})')

        if null_count > 0:
            print(f'\nAssigning FY ID {fy_id} to {null_count} cases with NULL fy_id...')

            # Update cases with NULL fy_id to current open FY
            cursor.execute('UPDATE cases SET fy_id = ? WHERE fy_id IS NULL', (fy_id,))
            conn.commit()

            print(f'Successfully updated {null_count} cases with FY ID {fy_id}')

            # Verify the fix
            cursor.execute('SELECT COUNT(*) FROM cases WHERE fy_id IS NULL')
            remaining_null = cursor.fetchone()[0]
            print(f'Cases with NULL fy_id after fix: {remaining_null}')

    else:
        print('\nNo current open financial year found - cannot assign fy_id values')

    conn.close()

if __name__ == "__main__":
    check_and_fix_fy_ids()