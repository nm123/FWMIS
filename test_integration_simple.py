#!/usr/bin/env python3
"""
Integration tests for FWMIS application using pytest
"""

import os
import sys
import sqlite3
import tempfile
import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.ui.dialogs.automated_testing.test_execution import TestExecutionManager

class MockDialog:
    pass

class TestIntegration:
    """Integration tests for database isolation and cross-module functionality."""

    @pytest.fixture
    def test_db_path(self):
        """Create a temporary test database path."""
        db_path = os.path.join(tempfile.gettempdir(), 'test_integration.db')
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_database_isolation(self, test_db_path):
        """Test that database isolation works correctly."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        # Verify the database file was created
        assert os.path.exists(test_db_path), "Test database should be created"

        # Test database connection
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['cases', 'financial_years', 'periods', 'responsibilities', 'write_off_annexures']
        for table in required_tables:
            assert table in tables, f"Required table '{table}' should exist"

        # Check that we have sample data
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        assert case_count > 0, "Should have sample case data"

        cursor.execute("SELECT COUNT(*) FROM financial_years")
        fy_count = cursor.fetchone()[0]
        assert fy_count > 0, "Should have financial year data"

        cursor.execute("SELECT COUNT(*) FROM responsibilities")
        resp_count = cursor.fetchone()[0]
        assert resp_count > 0, "Should have responsibility data"

        conn.close()

    def test_cross_module_data_consistency(self, test_db_path):
        """Test that data is consistent across different modules/tables."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check that all cases have valid fy_id references
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE fy_id NOT IN (SELECT id FROM financial_years)
        """)
        orphaned_cases = cursor.fetchone()[0]
        assert orphaned_cases == 0, f"Found {orphaned_cases} cases with invalid fy_id references"

        # Check that all cases have valid responsibility_id references
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE responsibility_id NOT IN (SELECT id FROM responsibilities)
        """)
        invalid_resp_cases = cursor.fetchone()[0]
        assert invalid_resp_cases == 0, f"Found {invalid_resp_cases} cases with invalid responsibility_id references"

        # Check that financial years have valid periods
        cursor.execute("""
            SELECT COUNT(*) FROM periods
            WHERE fy_id NOT IN (SELECT id FROM financial_years)
        """)
        orphaned_periods = cursor.fetchone()[0]
        assert orphaned_periods == 0, f"Found {orphaned_periods} periods with invalid fy_id references"

        conn.close()

    def test_module_interaction_simulation(self, test_db_path):
        """Test simulated interactions between different modules."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Simulate a case moving through different lists/statuses
        # Start with a case in Checklist
        cursor.execute("""
            SELECT id, transaction_no FROM cases
            WHERE list = 'Checklist' AND status = 'Alleged'
            LIMIT 1
        """)
        test_case = cursor.fetchone()

        if test_case:
            case_id, transaction_no = test_case

            # Simulate status change (this would normally be done by workflow_utils)
            cursor.execute(
                "UPDATE cases SET status = 'Confirmed' WHERE id = ?",
                (case_id,)
            )

            # Verify the change
            cursor.execute("SELECT status FROM cases WHERE id = ?", (case_id,))
            new_status = cursor.fetchone()[0]
            assert new_status == 'Confirmed', f"Status should be 'Confirmed', got '{new_status}'"

            # Simulate list change
            cursor.execute(
                "UPDATE cases SET list = 'Lead Schedule' WHERE id = ?",
                (case_id,)
            )

            # Verify the list change
            cursor.execute("SELECT list FROM cases WHERE id = ?", (case_id,))
            new_list = cursor.fetchone()[0]
            assert new_list == 'Lead Schedule', f"List should be 'Lead Schedule', got '{new_list}'"

        conn.commit()
        conn.close()

    def test_data_import_export_simulation(self, test_db_path):
        """Test simulated data import/export operations."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Simulate importing new cases
        new_cases = [
            ('IMPORT001', 'IMPORT001', 'Imported case 1', 5000.00, 'Alleged', 1, 1, 'Test Debtor 1', 'Test Category', 'Checklist'),
            ('IMPORT002', 'IMPORT002', 'Imported case 2', 7500.00, 'Alleged', 1, 1, 'Test Debtor 2', 'Test Category', 'Checklist'),
        ]

        cursor.executemany("""
            INSERT INTO cases (
                transaction_no, base_transaction_no, description, amount,
                status, fy_id, responsibility_id, debtor_name, category, list
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, new_cases)

        conn.commit()

        # Verify imports
        cursor.execute("SELECT COUNT(*) FROM cases WHERE transaction_no LIKE 'IMPORT%'")
        import_count = cursor.fetchone()[0]
        assert import_count == 2, f"Should have imported 2 cases, got {import_count}"

        # Simulate export (count records that would be exported)
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE list = 'Checklist' AND status IN ('Alleged', 'Confirmed')
        """)
        export_count = cursor.fetchone()[0]
        assert export_count >= 2, f"Should have at least 2 cases available for export, got {export_count}"

        conn.close()

    def test_concurrent_access_simulation(self, test_db_path):
        """Test simulated concurrent access to database."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        import threading
        import time

        results = {'success_count': 0, 'error_count': 0}
        results_lock = threading.Lock()

        def worker_thread(thread_id):
            """Simulate a worker thread accessing the database."""
            try:
                conn = sqlite3.connect(test_db_path, timeout=10.0)
                cursor = conn.cursor()

                # Perform some database operations
                cursor.execute("SELECT COUNT(*) FROM cases")
                count = cursor.fetchone()[0]

                # Simulate some work
                time.sleep(0.01)

                # Update a case (with thread safety)
                cursor.execute("""
                    UPDATE cases SET description = ?
                    WHERE id = (SELECT id FROM cases LIMIT 1)
                """, (f"Updated by thread {thread_id}",))

                conn.commit()
                conn.close()

                with results_lock:
                    results['success_count'] += 1

            except Exception as e:
                with results_lock:
                    results['error_count'] += 1

        # Run multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker_thread, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify results
        assert results['success_count'] == 5, f"All 5 threads should succeed, got {results['success_count']} successes"
        assert results['error_count'] == 0, f"No threads should fail, got {results['error_count']} failures"
