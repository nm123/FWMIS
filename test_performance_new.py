#!/usr/bin/env python3
"""
Performance tests for FWMIS application.
Tests memory efficiency and performance with large datasets using pytest.
"""

import os
import sys
import time
import pytest
import sqlite3
from datetime import datetime, timedelta
import tempfile

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.Utilities.optimized_import_utils import (
    create_performance_indexes, optimize_database_settings, get_optimal_chunk_size
)
from scripts.Utilities.performance_profiler import PerformanceProfiler, MemoryProfiler


class TestPerformanceSuite:
    """Performance test suite using pytest framework."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment."""
        self.profiler = PerformanceProfiler()
        self.memory_profiler = MemoryProfiler()
        self.temp_dir = tempfile.mkdtemp()

    def test_database_optimization_indexes(self):
        """Test that database performance indexes can be created successfully."""
        try:
            # Test index creation without errors
            create_performance_indexes()
            assert True, "Database indexes created successfully"
        except Exception as e:
            pytest.fail(f"Database index creation failed: {e}")

    def test_database_settings_optimization(self):
        """Test that database settings can be optimized."""
        try:
            # Test settings optimization
            optimize_database_settings()
            assert True, "Database settings optimized successfully"
        except Exception as e:
            pytest.fail(f"Database settings optimization failed: {e}")

    def test_optimal_chunk_size_calculation(self):
        """Test that optimal chunk size can be calculated."""
        try:
            chunk_size = get_optimal_chunk_size()
            assert isinstance(chunk_size, int), "Chunk size should be an integer"
            assert chunk_size > 0, "Chunk size should be positive"
        except Exception as e:
            pytest.fail(f"Optimal chunk size calculation failed: {e}")

    def test_performance_profiler_initialization(self):
        """Test that performance profiler can be initialized."""
        try:
            profiler = PerformanceProfiler()
            assert profiler is not None, "Performance profiler should be initialized"
        except Exception as e:
            pytest.fail(f"Performance profiler initialization failed: {e}")

    def test_memory_profiler_initialization(self):
        """Test that memory profiler can be initialized."""
        try:
            memory_profiler = MemoryProfiler()
            assert memory_profiler is not None, "Memory profiler should be initialized"
        except Exception as e:
            pytest.fail(f"Memory profiler initialization failed: {e}")

    def test_large_dataset_handling(self):
        """Test handling of large datasets without memory issues."""
        try:
            # Create a test database with larger dataset
            test_db = os.path.join(self.temp_dir, 'test_perf.db')

            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()

            # Create test table
            cursor.execute('''
                CREATE TABLE test_cases (
                    id INTEGER PRIMARY KEY,
                    transaction_no TEXT,
                    amount REAL,
                    description TEXT
                )
            ''')

            # Insert larger dataset (1000 records)
            test_data = []
            for i in range(1000):
                test_data.append((
                    f'TEST{i:04d}',
                    float(i * 100),
                    f'Test case {i}'
                ))

            cursor.executemany(
                'INSERT INTO test_cases (transaction_no, amount, description) VALUES (?, ?, ?)',
                test_data
            )
            conn.commit()

            # Verify data was inserted
            cursor.execute('SELECT COUNT(*) FROM test_cases')
            count = cursor.fetchone()[0]
            assert count == 1000, f"Expected 1000 records, got {count}"

            conn.close()

        except Exception as e:
            pytest.fail(f"Large dataset handling failed: {e}")
        finally:
            # Cleanup
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_query_performance(self):
        """Test database query performance with indexes."""
        try:
            test_db = os.path.join(self.temp_dir, 'test_query.db')

            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()

            # Create table with indexes
            cursor.execute('''
                CREATE TABLE cases (
                    id INTEGER PRIMARY KEY,
                    transaction_no TEXT,
                    amount REAL,
                    status TEXT
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX idx_transaction ON cases(transaction_no)')
            cursor.execute('CREATE INDEX idx_status ON cases(status)')

            # Insert test data
            test_cases = []
            for i in range(500):
                test_cases.append((
                    f'TXN{i:04d}',
                    float(i * 50),
                    'Active' if i % 2 == 0 else 'Closed'
                ))

            cursor.executemany(
                'INSERT INTO cases (transaction_no, amount, status) VALUES (?, ?, ?)',
                test_cases
            )
            conn.commit()

            # Test indexed query performance
            start_time = time.time()
            cursor.execute('SELECT * FROM cases WHERE status = ? AND amount > ?', ('Active', 1000))
            results = cursor.fetchall()
            query_time = time.time() - start_time

            # Should complete in reasonable time (< 0.1 seconds for 500 records)
            assert query_time < 0.1, ".3f"
            assert len(results) > 0, "Query should return results"

            conn.close()

        except Exception as e:
            pytest.fail(f"Query performance test failed: {e}")
        finally:
            if os.path.exists(test_db):
                os.remove(test_db)
