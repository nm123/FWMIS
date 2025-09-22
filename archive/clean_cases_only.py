#!/usr/bin/env python3
"""
Script to clean all cases from the database while preserving all other data
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Try relative imports first, fall back to absolute
try:
    from Utilities.config import DB_PATH
except ImportError:
    from scripts.Utilities.config import DB_PATH

import sqlite3


def clean_all_cases():
    """Delete all cases from the database while preserving other data"""
    print("Cleaning all cases from database...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get count of cases before deletion
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        print(f"Found {case_count} cases in database")

        # Delete all cases
        cursor.execute("DELETE FROM cases")
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} cases")

        # Reset auto-increment counter for cases table
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cases'")
        print("Reset auto-increment counter for cases table")

        # Also clean up any related audit logs for cases
        cursor.execute("DELETE FROM audit_logs WHERE details LIKE '%case%'")
        audit_deleted = cursor.rowcount
        print(f"Deleted {audit_deleted} related audit log entries")

        # Commit changes
        conn.commit()
        conn.close()

        print("Successfully cleaned all cases from database")
        print("All other data (responsibilities, categories, lists, etc.) preserved")
        return True

    except Exception as e:
        print(f"Error cleaning cases: {e}")
        return False


def verify_cleanup():
    """Verify that cases were cleaned but other data remains"""
    print("\nVerifying cleanup...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check cases table
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        print(f"Cases remaining: {case_count}")

        # Check other important tables
        tables_to_check = [
            "responsibilities",
            "categories",
            "lists",
            "financial_years",
            "periods",
            "audit_logs",
        ]

        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} records")

        conn.close()

        if case_count == 0:
            print("Cleanup successful - no cases remaining")
        else:
            print(f"Warning: {case_count} cases still remain")

        return True

    except Exception as e:
        print(f"Error verifying cleanup: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("CLEANING ALL CASES FROM DATABASE")
    print("=" * 60)
    print("WARNING: This will delete ALL cases from the database!")
    print("Other data (responsibilities, categories, lists, etc.) will be preserved")
    print()

    # Confirm action - automatically proceed for testing
    print("Automatically proceeding with cleanup for testing purposes...")
    print()

    # Clean cases
    success = clean_all_cases()

    if success:
        # Verify cleanup
        verify_cleanup()

    print("\n" + "=" * 60)
    if success:
        print("Database cleanup completed successfully!")
    else:
        print("Database cleanup failed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
