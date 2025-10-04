#!/usr/bin/env python3
"""
Schema Migration Script for FWMIS
Adds missing columns to responsibilities and financial_years tables,
and creates necessary indexes.
"""

import sqlite3
import sys
import os

# Add scripts to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.Utilities.config import DB_PATH

def migrate_schema():
    """Perform schema migration: add missing columns and indexes."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("Starting schema migration...")

        # 1. Add missing columns to responsibilities table
        print("\n=== Adding columns to responsibilities table ===")
        cursor.execute("PRAGMA table_info(responsibilities)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        if 'parent_id' not in existing_columns:
            cursor.execute("ALTER TABLE responsibilities ADD COLUMN parent_id INTEGER")
            print("Added parent_id column to responsibilities")
        else:
            print("parent_id column already exists in responsibilities")

        if 'is_posting_level' not in existing_columns:
            cursor.execute("ALTER TABLE responsibilities ADD COLUMN is_posting_level BOOLEAN DEFAULT 0")
            print("Added is_posting_level column to responsibilities")
        else:
            print("is_posting_level column already exists in responsibilities")

        if 'contacts' not in existing_columns:
            cursor.execute("ALTER TABLE responsibilities ADD COLUMN contacts TEXT DEFAULT '[]'")
            print("Added contacts column to responsibilities")
        else:
            print("contacts column already exists in responsibilities")

        # 2. Add missing columns to financial_years table
        print("\n=== Adding columns to financial_years table ===")
        cursor.execute("PRAGMA table_info(financial_years)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        if 'active_period' not in existing_columns:
            cursor.execute("ALTER TABLE financial_years ADD COLUMN active_period INTEGER DEFAULT 0")
            print("Added active_period column to financial_years with default 0")
        else:
            print("active_period column already exists in financial_years")

        # Set a default active_period: set the latest open FY to 1 if none is set
        cursor.execute("""
            UPDATE financial_years 
            SET active_period = 1 
            WHERE status = 'open' 
            AND active_period = 0 
            AND id = (SELECT MAX(id) FROM financial_years WHERE status = 'open')
        """)
        updated = cursor.rowcount
        if updated > 0:
            print(f"Set active_period=1 for {updated} open financial year(s)")
        else:
            print("No open financial years to set as active")

        # 3. Create indexes after adding columns
        print("\n=== Creating indexes ===")

        # Index on responsibilities.parent_id
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_responsibilities_parent_id ON responsibilities(parent_id)")
            print("Created index idx_responsibilities_parent_id")
        except sqlite3.Error as e:
            print(f"Warning: Failed to create idx_responsibilities_parent_id: {e}")

        # Index on financial_years.active_period (optional, but useful for queries)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_years_active_period ON financial_years(active_period)")
            print("Created index idx_financial_years_active_period")
        except sqlite3.Error as e:
            print(f"Warning: Failed to create idx_financial_years_active_period: {e}")

        # Ensure other essential indexes exist (from database_optimizer)
        essential_indexes = [
            ("idx_cases_fy", "cases", "fy_id"),  # Relevant for FY operations
        ]
        for index_name, table, column in essential_indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                print(f"Ensured index: {index_name}")
            except sqlite3.Error as e:
                print(f"Warning: Failed to ensure {index_name}: {e}")

        conn.commit()
        print("\nSchema migration completed successfully!")

    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_schema()