#!/usr/bin/env python3
"""
Test script to debug database optimizer self error
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_db_optimizer():
    try:
        from scripts.Utilities.database_optimizer import DatabaseOptimizer

        # Create a test database path
        test_db_path = str(Path(__file__).parent / "data" / "fruitless.db")

        print(f"Creating DatabaseOptimizer with path: {test_db_path}")

        # Create optimizer instance
        optimizer = DatabaseOptimizer(test_db_path)
        print("DatabaseOptimizer instance created successfully")

        # Try to call get_database_stats
        print("Calling get_database_stats...")
        stats = optimizer.get_database_stats()
        print(f"Stats retrieved: {len(stats)} items")

        # Try to call create_performance_indexes
        print("Calling create_performance_indexes...")
        optimizer.create_performance_indexes()
        print("Indexes created successfully")

        print("[SUCCESS] All database optimizer operations completed successfully")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_optimizer()
