#!/usr/bin/env python3
"""
Test script to verify database index creation works
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

# Create a test database with the correct schema
import tempfile
import sqlite3
import shutil

def test_index_creation():
    # Create test database
    temp_dir = Path(tempfile.gettempdir())
    test_db_path = temp_dir / "test_index.db"

    # Copy from existing database if available
    original_db = Path(__file__).parent / "data" / "fruitless.db"
    if original_db.exists():
        shutil.copy2(original_db, test_db_path)
        print(f"Copied existing database to {test_db_path}")
    else:
        # Create fresh database with schema
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                base_transaction_no TEXT UNIQUE,
                assessment_status TEXT DEFAULT 'Alleged',
                lc_status TEXT,
                suffixes TEXT,
                fy_id INTEGER,
                amount REAL,
                debtor_name TEXT,
                vendor_name TEXT,
                is_finalized INTEGER DEFAULT 0,
                finalized_date TEXT,
                finalization_reason TEXT,
                evidence_paths TEXT,
                write_off_group_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add some test data
        cursor.execute("INSERT INTO cases (base_transaction_no, amount) VALUES ('TEST-001', 1000.0)")
        conn.commit()
        conn.close()
        print(f"Created fresh test database at {test_db_path}")

    # Now test the optimizer
    try:
        from scripts.Utilities.database_optimizer import DatabaseOptimizer
        optimizer = DatabaseOptimizer(str(test_db_path))

        print("Testing index creation...")
        optimizer.create_performance_indexes()

        # Check what indexes were created
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        conn.close()

        print(f"Created indexes: {[idx[0] for idx in indexes]}")

        # Check if created_at column exists
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(cases)")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        print(f"Available columns: {column_names}")

        if 'created_at' in column_names:
            print("[SUCCESS] created_at column exists")
        else:
            print("[ERROR] created_at column missing")

        if 'idx_cases_created' in [idx[0] for idx in indexes]:
            print("[SUCCESS] idx_cases_created index created")
        else:
            print("[WARNING] idx_cases_created index not created")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        if test_db_path.exists():
            test_db_path.unlink()
            print(f"Cleaned up test database: {test_db_path}")

if __name__ == "__main__":
    test_index_creation()
