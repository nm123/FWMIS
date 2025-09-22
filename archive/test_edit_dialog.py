#!/usr/bin/env python3
"""
Test script to verify EditCaseDialog can be instantiated correctly
"""
import os
import sqlite3
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

try:
    from scripts.Utilities.config import DB_PATH
except ImportError:
    # Fallback path
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "fruitless.db")


def test_edit_case_dialog():
    """Test that EditCaseDialog can be instantiated without errors"""
    print("=== Testing EditCaseDialog Instantiation ===")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    try:
        # Import required modules
        from PyQt5.QtWidgets import QApplication
        from scripts.case_management_modules.edit_case_dialog import \
            EditCaseDialog

        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Get a case from the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases LIMIT 1")
        case_data = cursor.fetchone()
        conn.close()

        if not case_data:
            print("ERROR: No case data found")
            return False

        print(f"Case data type: {type(case_data)}")
        print(f"Case data length: {len(case_data)}")
        print(f"Case ID: {case_data[0]}")
        print(f"Transaction No: {case_data[1]}")

        # Try to create EditCaseDialog
        print("Creating EditCaseDialog...")
        try:
            dialog = EditCaseDialog(case_data)
            print("SUCCESS: EditCaseDialog created without errors")
            dialog.close()  # Close the dialog
            return True
        except Exception as e:
            print(f"ERROR: Failed to create EditCaseDialog: {e}")
            import traceback

            traceback.print_exc()
            return False

    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing EditCaseDialog")
    print("=" * 50)

    success = test_edit_case_dialog()

    if success:
        print("\nSUCCESS: EditCaseDialog can be instantiated correctly!")
    else:
        print("\nFAILED: EditCaseDialog instantiation failed!")
        sys.exit(1)
