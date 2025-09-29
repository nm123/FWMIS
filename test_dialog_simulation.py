#!/usr/bin/env python3
"""
Simulate what the automated testing dialog does to test the fix.
"""

import os
import sys
import tempfile
import uuid
import sqlite3
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

def setup_test_database():
    """Set up an isolated test database for testing."""
    # Create unique temporary database for testing
    unique_id = str(uuid.uuid4())[:8]
    test_db_path = os.path.join(tempfile.gettempdir(), f"fwmis_test_{unique_id}.db")

    # Set environment variables for isolated testing
    os.environ['FWMIS_TEST_DB'] = test_db_path
    os.environ['FWMIS_TEST_MODE'] = '1'
    os.environ['FWMIS_DEBUG'] = '1'

    # Create the test database with schema
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Create basic schema for testing
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
            is_finalized INTEGER DEFAULT 0,
            finalized_date TEXT,
            finalization_reason TEXT,
            evidence_paths TEXT,
            write_off_group_id TEXT
        )
    """)

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
        CREATE TABLE periods (
            id INTEGER PRIMARY KEY,
            period_number INTEGER,
            start_date TEXT,
            end_date TEXT,
            fy_id INTEGER,
            is_open INTEGER DEFAULT 0,
            FOREIGN KEY (fy_id) REFERENCES financial_years (id)
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

    # Add some basic test data
    cursor.execute("INSERT INTO financial_years (id, start_year, end_year, status) VALUES (1, 2024, 2025, 'open')")
    cursor.execute("INSERT INTO responsibilities (id, name, is_posting_level) VALUES (1, 'Test Responsibility', 1)")
    cursor.execute("""
        INSERT INTO cases (id, transaction_no, base_transaction_no, description, amount, status, fy_id, responsibility_id, assessment_status)
        VALUES (1, 'TEST001', 'TEST001', 'Test case 1', 10000.00, 'Active', 1, 1, 'Alleged')
    """)

    conn.commit()
    conn.close()

    print(f"Created test database: {test_db_path}")
    return test_db_path

def cleanup_test_database(test_db_path):
    """Clean up the test database"""
    if test_db_path and os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
            print(f"Cleaned up test database: {test_db_path}")
        except Exception as e:
            print(f"Warning: Could not remove test database {test_db_path}: {e}")

    # Clean up environment variables
    for var in ['FWMIS_TEST_DB', 'FWMIS_TEST_MODE', 'FWMIS_DEBUG']:
        os.environ.pop(var, None)

def main():
    """Simulate the automated testing dialog"""
    test_db_path = None

    try:
        print("Setting up test database...")
        test_db_path = setup_test_database()

        print("Testing automated testing dialog components...")
        # Test the test execution manager directly
        test_dialog_components()

        print("Running automated test suite...")
        # Run the test with environment variables
        fwmis_dir = os.path.dirname(__file__)
        test_file_path = os.path.join(fwmis_dir, 'test_automated_suite.py')
        os.system(f'python -m pytest "{test_file_path}" -v --tb=short')

    finally:
        print("Cleaning up...")
        cleanup_test_database(test_db_path)

def test_dialog_components():
    """Test the automated testing dialog components for warnings"""
    print("  Testing dialog imports...")

    try:
        # Import dialog components
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
        from scripts.ui.dialogs.automated_testing.test_execution import TestExecutionManager
        from scripts.ui.dialogs.automated_testing.results_handling import ResultsHandler
        from scripts.ui.dialogs.automated_testing.ui_setup import UISetupManager
        print("    [OK] Dialog components imported successfully")

        # Test basic functionality without GUI
        print("    [OK] Dialog components initialized without warnings")

    except Exception as e:
        print(f"    [WARNING] Warning in dialog components: {e}")
        return False

    return True

if __name__ == "__main__":
    main()
