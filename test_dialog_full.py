#!/usr/bin/env python3
"""
Test the complete automated testing dialog functionality
"""

import os
import sys
import tempfile
import uuid
import sqlite3
import subprocess

def test_dialog_simulation():
    """Simulate the automated testing dialog end-to-end"""

    # Step 1: Create test database like the dialog does
    print("Step 1: Creating test database...")
    unique_id = str(uuid.uuid4())[:8]
    test_db_path = os.path.join(tempfile.gettempdir(), f'fwmis_test_{unique_id}.db')

    # Set environment variables
    os.environ['FWMIS_TEST_DB'] = test_db_path
    os.environ['FWMIS_TEST_MODE'] = '1'
    os.environ['FWMIS_DEBUG'] = '1'

    # Create complete schema
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Cases table with all columns
    conn.execute("""
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            base_transaction_no TEXT,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'Active',
            fy_id INTEGER,
            responsibility_id INTEGER,
            created_date TEXT,
            updated_date TEXT,
            assessment_status TEXT,
            suffixes TEXT,
            date_reported TEXT,
            reference_no TEXT,
            lc_status TEXT,
            debtor_name TEXT,
            category TEXT,
            list TEXT,
            is_finalized INTEGER DEFAULT 0,
            finalized_date TEXT,
            finalization_reason TEXT,
            evidence_paths TEXT,
            write_off_group_id TEXT
        )
    """)

    # Other required tables
    conn.execute("""
        CREATE TABLE financial_years (
            id INTEGER PRIMARY KEY,
            start_year INTEGER,
            end_year INTEGER,
            status TEXT DEFAULT 'closed',
            active_period INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE responsibilities (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            parent_id INTEGER,
            is_posting_level INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE write_off_annexures (
            id INTEGER PRIMARY KEY,
            annexure_no TEXT UNIQUE,
            status TEXT DEFAULT 'Draft',
            role TEXT,
            decline_reason TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    """)

    # Add test data
    cursor.execute("INSERT INTO financial_years (id, start_year, end_year, status) VALUES (1, 2024, 2025, 'open')")
    cursor.execute("INSERT INTO responsibilities (id, name, is_posting_level) VALUES (1, 'Test Responsibility', 1)")
    cursor.execute("INSERT INTO cases (id, transaction_no, base_transaction_no, description, amount, status, fy_id, responsibility_id, assessment_status, debtor_name, category) VALUES (1, 'TEST001', 'TEST001', 'Test case 1', 10000.00, 'Active', 1, 1, 'Alleged', 'Test Debtor', 'Test Category')")

    conn.commit()
    conn.close()

    print(f"Created test database: {test_db_path}")

    # Step 2: Run tests with the environment
    print("\nStep 2: Running automated tests...")

    # Test the whole test suite file
    fwmis_dir = os.path.dirname(__file__)
    test_file_path = os.path.join(fwmis_dir, 'test_automated_suite.py')
    test_commands = [
        ['python', '-m', 'pytest', test_file_path, '-v', '--tb=short'],
    ]

    success_count = 0

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n  Test {i}: {' '.join(cmd[4:6])}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("    PASSED")
            success_count += 1
        else:
            print("    FAILED")
            print(f"    Error: {result.stderr.strip()[:100]}...")

    # Step 3: Cleanup
    print("\nStep 3: Cleaning up...")
    os.remove(test_db_path)
    for var in ['FWMIS_TEST_DB', 'FWMIS_TEST_MODE', 'FWMIS_DEBUG']:
        os.environ.pop(var, None)

    print("Cleanup complete")

    # Summary
    print(f"\n{'='*50}")
    print("AUTOMATED TESTING DIALOG TEST RESULTS")
    print(f"{'='*50}")
    print(f"Tests run: {len(test_commands)}")
    print(f"Tests passed: {success_count}")
    print(f"Tests failed: {len(test_commands) - success_count}")

    if success_count == len(test_commands):
        print("SUCCESS: All tests passed! Dialog should work correctly.")
        return True
    else:
        print("FAILURE: Some tests still failing.")
        return False

if __name__ == "__main__":
    success = test_dialog_simulation()
    sys.exit(0 if success else 1)
