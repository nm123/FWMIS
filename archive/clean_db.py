#!/usr/bin/env python3
"""
Database cleanup utility for FWMIS
Provides functions to clean up test data and orphaned records
"""

import argparse
import os
import sqlite3
import sys
from typing import Optional

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(scripts_dir)

try:
    from Utilities.config import DB_PATH
except ImportError:
    # Fallback if config.py is missing
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )
    DB_PATH = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Warning: config.py not found, using fallback paths: {DB_PATH}")


def clean_responsibility_by_id(resp_id: int, dry_run: bool = False) -> bool:
    """
    Clean up a specific responsibility and its associated contacts

    Args:
        resp_id: The responsibility ID to clean up
        dry_run: If True, only show what would be deleted without actually deleting

    Returns:
        True if successful, False otherwise
    """
    if not isinstance(resp_id, int) or resp_id <= 0:
        print(f"Error: Invalid responsibility ID: {resp_id}")
        return False

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")

        # Check if responsibility exists
        cursor.execute("SELECT id, name FROM responsibilities WHERE id = ?", (resp_id,))
        resp = cursor.fetchone()

        if not resp:
            print(f"Warning: Responsibility ID {resp_id} not found")
            return True

        print(f"Found responsibility: ID={resp[0]}, Name='{resp[1]}'")

        # Count associated contacts
        cursor.execute(
            "SELECT COUNT(*) FROM contacts WHERE responsibility_id = ?", (resp_id,)
        )
        contact_count = cursor.fetchone()[0]
        print(f"Found {contact_count} associated contacts")

        if dry_run:
            print("DRY RUN - No changes made")
            return True

        # Delete contacts first (foreign key constraint)
        if contact_count > 0:
            cursor.execute(
                "DELETE FROM contacts WHERE responsibility_id = ?", (resp_id,)
            )
            print(f"Deleted {contact_count} contacts")

        # Delete responsibility
        cursor.execute("DELETE FROM responsibilities WHERE id = ?", (resp_id,))
        print(f"Deleted responsibility ID {resp_id}")

        conn.commit()
        print("Cleanup completed successfully")
        return True

    except sqlite3.Error as e:
        print(f"Database error during cleanup: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during cleanup: {e}")
        return False
    finally:
        if conn:
            conn.close()


def list_responsibilities(limit: Optional[int] = None) -> None:
    """List all responsibilities in the database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = "SELECT id, name, parent_id, is_posting_level FROM responsibilities ORDER BY id"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        responsibilities = cursor.fetchall()

        if not responsibilities:
            print("No responsibilities found")
            return

        print(f"{'ID':<5} {'Name':<50} {'Parent':<8} {'Posting':<8}")
        print("-" * 75)
        for resp in responsibilities:
            parent = str(resp[2]) if resp[2] else "None"
            posting = "Yes" if resp[3] else "No"
            print(f"{resp[0]:<5} {resp[1]:<50} {parent:<8} {posting:<8}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(description="FWMIS Database Cleanup Utility")
    parser.add_argument("--resp-id", type=int, help="Responsibility ID to clean up")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument("--list", action="store_true", help="List all responsibilities")
    parser.add_argument(
        "--limit", type=int, help="Limit number of responsibilities to list"
    )

    args = parser.parse_args()

    if args.list:
        list_responsibilities(args.limit)
    elif args.resp_id:
        success = clean_responsibility_by_id(args.resp_id, args.dry_run)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
