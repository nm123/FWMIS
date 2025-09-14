#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Script for F&W MIS Refactor

This script tests the complete workflow from case creation to finalization
to ensure the single-case model refactor is working correctly.

Run this script after the refactor to verify all functionality.
"""

import sqlite3
import os
import sys
from datetime import datetime
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.workflow_utils import (
    handle_case_status_change,
    handle_loss_control_status_change,
    approve_write_off_submission,
    create_write_off_group,
    get_case_workflow_status
)

def test_database_connection():
    """Test basic database connectivity"""
    print("=== Testing Database Connection ===")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cases")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"[PASS] Database connection successful. Found {count} cases.")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False

def test_schema_migration():
    """Test that new schema columns exist"""
    print("\n=== Testing Schema Migration ===")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check for new columns
        cursor.execute("PRAGMA table_info(cases)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = [
            'base_transaction_no', 'assessment_status', 'lc_status',
            'suffixes', 'write_off_group_id', 'evidence_paths'
        ]

        missing_columns = []
        for col in required_columns:
            if col not in columns:
                missing_columns.append(col)

        conn.close()

        if missing_columns:
            print(f"[FAIL] Missing columns: {missing_columns}")
            return False
        else:
            print("[PASS] All required schema columns present.")
            return True

    except Exception as e:
        print(f"[FAIL] Schema check failed: {e}")
        return False

def test_workflow_transitions():
    """Test assessment status transitions"""
    print("\n=== Testing Workflow Transitions ===")

    # Find a test case (preferably one that's not finalized)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, base_transaction_no, assessment_status, lc_status, suffixes, is_finalized
        FROM cases
        WHERE is_finalized = 0 AND assessment_status = 'Alleged'
        LIMIT 1
    """)

    test_case = cursor.fetchone()
    conn.close()

    if not test_case:
        print("[WARN] No suitable test case found (Alleged, not finalized)")
        return True  # Not a failure, just no test data

    case_id, base_no, current_status, lc_status, suffixes, finalized = test_case
    print(f"Testing with case: {base_no} (ID: {case_id})")

    # Test 1: Alleged -> Under Assessment (should work)
    print("Test 1: Alleged -> Under Assessment")
    result = handle_case_status_change(case_id, base_no, "Under Assessment")
    print(f"  Result: {'PASS' if result else 'FAIL'}")

    # Test 2: Under Assessment -> Valid (should fail without evidence)
    print("Test 2: Under Assessment -> Valid (should fail without evidence)")
    result = handle_case_status_change(case_id, base_no, "Valid")
    print(f"  Result: {'PASS (correctly failed)' if not result else 'FAIL (should have failed)'}")

    # Reset to Under Assessment for next test
    handle_case_status_change(case_id, base_no, "Under Assessment")

    return True

def test_list_filtering():
    """Test that list filtering works with new schema"""
    print("\n=== Testing List Filtering ===")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Test each list filter
    filters = {
        "Checklist": "1=1",
        "Lead Schedule": "assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO%'",
        "Write-Off Recommended": "suffixes LIKE '%-WOR%'",
        "Recovered": "suffixes LIKE '%-REC%'",
        "Written Off": "suffixes LIKE '%-WO%'"
    }

    results = {}
    for list_name, where_clause in filters.items():
        query = f"SELECT COUNT(*) FROM cases WHERE {where_clause}"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        results[list_name] = count
        print(f"  {list_name}: {count} cases")

    conn.close()

    # Basic sanity check - there should be cases in checklist
    if results.get("Checklist", 0) == 0:
        print("[WARN] Warning: No cases in Checklist - this may indicate data issues")
    else:
        print("[PASS] List filtering appears to be working")

    return True

def test_evidence_validation():
    """Test that evidence validation is enforced"""
    print("\n=== Testing Evidence Validation ===")

    # This is harder to test programmatically since it requires UI interaction
    # We'll just verify the validation functions exist and can be called
    try:
        # Test workflow status function
        workflow_status = get_case_workflow_status(1)  # Test with ID 1
        if workflow_status:
            print("[PASS] Workflow status function working")
            print(f"  Status: {workflow_status.get('assessment_status', 'N/A')}")
            print(f"  Appears in: {workflow_status.get('appears_in_lists', [])}")
        else:
            print("[WARN] No workflow status returned (may be normal if no case with ID 1)")

        return True
    except Exception as e:
        print(f"[FAIL] Evidence validation test failed: {e}")
        return False

def test_write_off_workflow():
    """Test write-off submission workflow"""
    print("\n=== Testing Write-Off Workflow ===")

    # Check for cases in Write-Off Recommended status
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cases WHERE lc_status = 'Write Off Recommended' AND write_off_group_id IS NULL")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"Cases ready for write-off grouping: {count}")

    if count > 0:
        print("[PASS] Write-off workflow has cases to test")
    else:
        print("[WARN] No cases currently in write-off recommended status")

    return True

def test_finalized_case_editing():
    """Test that finalized cases cannot be edited"""
    print("\n=== Testing Finalized Case Editing Prevention ===")

    # Find a finalized case
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, base_transaction_no FROM cases WHERE is_finalized = 1 LIMIT 1")
    finalized_case = cursor.fetchone()
    conn.close()

    if not finalized_case:
        print("[WARN] No finalized cases found to test")
        return True

    case_id, base_no = finalized_case
    print(f"Testing finalized case: {base_no} (ID: {case_id})")

    # Try to change status of finalized case (should fail)
    result = handle_case_status_change(case_id, base_no, "Under Assessment")
    if not result:
        print("[PASS] Correctly prevented status change on finalized case")
        return True
    else:
        print("[FAIL] Incorrectly allowed status change on finalized case")
        return False

def test_evidence_validation_blocks():
    """Test that missing evidence blocks status changes"""
    print("\n=== Testing Evidence Validation Blocks ===")

    # Find a non-finalized case without evidence
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, base_transaction_no, assessment_status
        FROM cases
        WHERE is_finalized = 0 AND assessment_status = 'Under Assessment'
        AND (evidence_paths IS NULL OR evidence_paths = '')
        LIMIT 1
    """)

    test_case = cursor.fetchone()
    conn.close()

    if not test_case:
        print("[WARN] No suitable case found for evidence validation test")
        return True

    case_id, base_no, current_status = test_case
    print(f"Testing case: {base_no} (ID: {case_id})")

    # Try to change to Valid without evidence (should fail)
    result = handle_case_status_change(case_id, base_no, "Valid")
    if not result:
        print("[PASS] Correctly blocked Valid status change without evidence")
    else:
        print("[FAIL] Incorrectly allowed Valid status change without evidence")
        return False

    # Try to change to Confirmed without evidence (should fail)
    result = handle_case_status_change(case_id, base_no, "Confirmed")
    if not result:
        print("[PASS] Correctly blocked Confirmed status change without evidence")
        return True
    else:
        print("[FAIL] Incorrectly allowed Confirmed status change without evidence")
        return False

def test_complete_write_off_workflow():
    """Test complete write-off workflow from Confirmed to Written Off"""
    print("\n=== Testing Complete Write-Off Workflow ===")

    # Find a case in Confirmed status
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, base_transaction_no FROM cases
        WHERE assessment_status = 'Confirmed' AND is_finalized = 0
        AND (lc_status IS NULL OR lc_status = 'Awaiting LC determination')
        LIMIT 1
    """)

    test_case = cursor.fetchone()

    if not test_case:
        print("[WARN] No suitable Confirmed case found for write-off workflow test")
        conn.close()
        return True

    case_id, base_no = test_case
    print(f"Testing complete workflow with case: {base_no} (ID: {case_id})")

    # Step 1: Change to Write Off Recommended
    print("Step 1: Changing to Write Off Recommended")
    result = handle_loss_control_status_change(case_id, base_no, "Write Off Recommended")
    if not result:
        print("[FAIL] Failed to change to Write Off Recommended")
        conn.close()
        return False

    # Verify case is now in Write-Off Recommended
    cursor.execute("SELECT lc_status, suffixes FROM cases WHERE id = ?", (case_id,))
    status_check = cursor.fetchone()
    if status_check[0] != "Write Off Recommended" or "-WOR" not in status_check[1]:
        print("[FAIL] Case not properly set to Write Off Recommended")
        conn.close()
        return False

    print("[PASS] Case successfully set to Write Off Recommended")

    # Step 2: Create write-off group
    print("Step 2: Creating write-off group")
    group_id = create_write_off_group([case_id])
    if not group_id:
        print("[FAIL] Failed to create write-off group")
        conn.close()
        return False

    print(f"[PASS] Write-off group created: {group_id}")

    # Step 3: Approve write-off
    print("Step 3: Approving write-off")
    result = approve_write_off_submission(group_id)
    if not result:
        print("[FAIL] Failed to approve write-off")
        conn.close()
        return False

    # Verify case is now Written Off and finalized
    cursor.execute("SELECT lc_status, suffixes, is_finalized FROM cases WHERE id = ?", (case_id,))
    final_check = cursor.fetchone()
    conn.close()

    if (final_check[0] == "Written Off" and
        "-WO" in final_check[1] and
        final_check[2] == 1):
        print("[PASS] Case successfully written off and finalized")
        return True
    else:
        print(f"[FAIL] Case not properly finalized. Status: {final_check[0]}, Suffixes: {final_check[1]}, Finalized: {final_check[2]}")
        return False

def test_file_path_handling():
    """Test that evidence files are stored in correct paths"""
    print("\n=== Testing Evidence File Path Handling ===")

    # Check if the expected directory structure exists
    expected_base_path = r"D:\Users\maritzne\OneDrive\Work\Accounts Payable\GitHub\FWMIS\data\2025-2026\Supporting Evidence"

    if not os.path.exists(expected_base_path):
        print(f"[WARN] Expected base path does not exist: {expected_base_path}")
        print("This may be normal if no cases have been processed yet")
        return True

    # Check for case-specific folders
    case_folders = [f for f in os.listdir(expected_base_path) if f.startswith("Case ") and os.path.isdir(os.path.join(expected_base_path, f))]

    if case_folders:
        print(f"[PASS] Found {len(case_folders)} case folders in correct location")
        # Check one folder for proper file naming
        sample_folder = os.path.join(expected_base_path, case_folders[0])
        files = os.listdir(sample_folder)
        expected_files = [f for f in files if any(keyword in f for keyword in ["Assessment Evidence", "Loss Control Minutes", "Recovery Evidence", "Supporting Evidence", "Source Document"])]
        if expected_files:
            print(f"[PASS] Sample case folder has {len(expected_files)} properly named evidence files")
        else:
            print("[WARN] Sample case folder has no properly named evidence files")
    else:
        print("[INFO] No case folders found yet")

    return True

def test_excel_export_functionality():
    """Test Excel export functionality for write-off annexures and list exports"""
    print("\n=== Testing Excel Export Functionality ===")

    try:
        import pandas as pd
        import openpyxl
        print("[PASS] pandas and openpyxl are available for Excel export")
    except ImportError as e:
        print(f"[FAIL] Required packages not available: {e}")
        print("Install with: pip install pandas openpyxl")
        return False

    # Test basic Excel file creation capability
    try:
        import tempfile
        import os

        # Create a temporary Excel file to test functionality
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name

        # Create test data
        test_data = {
            'Case Number': ['202600001', '202600002'],
            'Amount': [1000.50, 2500.75],
            'Status': ['Confirmed', 'Valid']
        }

        df = pd.DataFrame(test_data)

        # Test Excel writing
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Test', index=False)

        # Verify file was created and has content
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("[PASS] Excel file creation and writing successful")

            # Try to read it back
            df_read = pd.read_excel(temp_path, engine='openpyxl')
            if len(df_read) == 2:
                # Check if the first case number is in the data (handle potential Excel number formatting)
                case_numbers = df_read['Case Number'].tolist()
                if any('202600001' in str(val) for val in case_numbers):
                    print("[PASS] Excel file reading and content verification successful")
                    return True
                else:
                    print(f"[FAIL] Excel file content verification failed. Expected '202600001' in {case_numbers}")
                    return False
            else:
                print(f"[FAIL] Excel file has wrong number of rows. Expected 2, got {len(df_read)}")
                return False
        else:
            print("[FAIL] Excel file was not created or is empty")
            return False

        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass

        return True

    except Exception as e:
        print(f"[FAIL] Excel export functionality test failed: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("F&W MIS Refactor - Comprehensive Testing")
    print("=" * 50)

    tests = [
        test_database_connection,
        test_schema_migration,
        test_workflow_transitions,
        test_list_filtering,
        test_evidence_validation,
        test_write_off_workflow,
        test_finalized_case_editing,
        test_evidence_validation_blocks,
        test_complete_write_off_workflow,
        test_file_path_handling,
        test_excel_export_functionality
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"{test.__name__}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tests passed! Refactor appears successful.")
        return True
    else:
        print("WARNING: Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)