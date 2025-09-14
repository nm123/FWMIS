#!/usr/bin/env python3
"""
Test script to verify Edit button functionality
"""
import sys
import os
import sqlite3

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

try:
    from scripts.Utilities.config import DB_PATH
except ImportError:
    # Fallback path
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'fruitless.db')

def test_database_connection():
    """Test basic database connection and queries"""
    print("=== Testing Database Connection ===")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM cases")
        count = cursor.fetchone()[0]
        print(f"Total cases in database: {count}")

        if count == 0:
            print("WARNING: No cases found in database")
            return False

        # Test getting a sample case
        cursor.execute("SELECT * FROM cases LIMIT 1")
        sample_case = cursor.fetchone()

        if sample_case:
            print(f"Sample case has {len(sample_case)} columns")
            print(f"First few columns: {sample_case[:5]}")
            print(f"Case ID: {sample_case[0]}")
            print(f"Transaction No: {sample_case[1]}")
            print(f"Base Transaction No: {sample_case[9] if len(sample_case) > 9 else 'N/A'}")
        else:
            print("ERROR: Could not retrieve sample case")
            return False

        # Test the specific query used in edit_case_by_row
        display_case_no = sample_case[1]  # Use the transaction_no as display_case_no
        print(f"\n=== Testing Edit Button Query ===")
        print(f"Using display_case_no: '{display_case_no}'")

        # Try the exact query from edit_case_by_row
        cursor.execute("SELECT * FROM cases WHERE base_transaction_no = ? OR transaction_no = ?", (display_case_no, display_case_no))
        result = cursor.fetchone()

        if result:
            print("SUCCESS: Query found case data")
            print(f"Result has {len(result)} columns")
            print(f"Result ID: {result[0]}")
        else:
            print("WARNING: Query did not find case data")

            # Try with suffixes if no direct match
            if '-' not in str(display_case_no):
                print("Trying with suffixes...")
                for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                    cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (f"{display_case_no}{suffix}",))
                    result = cursor.fetchone()
                    if result:
                        print(f"SUCCESS: Found case with suffix {suffix}")
                        break

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_case_data_format():
    """Test the case data format expected by EditCaseDialog"""
    print("\n=== Testing Case Data Format ===")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get a case using SELECT *
        cursor.execute("SELECT * FROM cases LIMIT 1")
        case_data = cursor.fetchone()

        if not case_data:
            print("ERROR: No case data found")
            return False

        print(f"Case data type: {type(case_data)}")
        print(f"Case data length: {len(case_data)}")

        # Test the field extraction logic from EditCaseDialog
        case_id = case_data[0]
        print(f"case_id: {case_id}")

        # Test tuple indexing (using correct column indices from database schema)
        base_transaction_no = case_data[41] if len(case_data) > 41 and case_data[41] else str(case_data[1]).split('-')[0]
        transaction_no = case_data[1] if len(case_data) > 1 else ''
        assessment_status = case_data[42] if len(case_data) > 42 else 'Alleged'
        lc_status = case_data[43] if len(case_data) > 43 else None
        suffixes = case_data[44] if len(case_data) > 44 else ''

        print(f"base_transaction_no: {base_transaction_no}")
        print(f"transaction_no: {transaction_no}")
        print(f"assessment_status: {assessment_status}")
        print(f"lc_status: {lc_status}")
        print(f"suffixes: {suffixes}")

        # Test dictionary access (should fail)
        try:
            dict_test = case_data.get('assessment_status')
            print(f"Dictionary access result: {dict_test}")
        except AttributeError as e:
            print(f"Dictionary access failed as expected: {e}")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Case data format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Edit Button Functionality")
    print("=" * 50)

    success1 = test_database_connection()
    success2 = test_case_data_format()

    if success1 and success2:
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[FAILED] Some tests failed!")
        sys.exit(1)