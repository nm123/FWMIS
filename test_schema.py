#!/usr/bin/env python3
"""
Test the database schema creation using pytest
"""

import os
import sys
import tempfile
import sqlite3
import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.ui.dialogs.automated_testing.test_execution import TestExecutionManager

class MockDialog:
    pass

class TestDatabaseSchema:
    """Test database schema creation and validation."""

    @pytest.fixture
    def test_db_path(self):
        """Create a unique temporary test database path."""
        import uuid
        db_path = os.path.join(tempfile.gettempdir(), f'test_schema_{uuid.uuid4().hex[:8]}.db')
        yield db_path
        # Cleanup with retry for Windows file locking
        import time
        for _ in range(10):
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                break
            except OSError:
                time.sleep(0.1)

    def test_schema_creation(self, test_db_path):
        """Test that the database schema can be created successfully."""
        manager = TestExecutionManager(MockDialog())

        # Create the test database
        manager._create_test_database(test_db_path)

        # Verify the database file was created
        assert os.path.exists(test_db_path), "Database file should be created"

        # Verify we can connect to the database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check that tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Should have the main tables
        expected_tables = ['cases', 'financial_years', 'responsibilities', 'write_off_annexures', 'write_off_annexure_cases', 'installments', 'periods']
        for table in expected_tables:
            assert table in tables, f"Table '{table}' should be created"

        conn.close()

    def test_cases_table_schema(self, test_db_path):
        """Test that the cases table has the correct schema."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check cases table columns
        cursor.execute("PRAGMA table_info(cases)")
        columns = [row[1] for row in cursor.fetchall()]

        # Required columns for the cases table
        required_cols = [
            'id', 'transaction_no', 'base_transaction_no', 'description', 'amount',
            'status', 'fy_id', 'responsibility_id', 'created_date', 'updated_date',
            'assessment_status', 'suffixes', 'date_reported', 'reference_no', 'lc_status',
            'debtor_name', 'category', 'list', 'is_finalized', 'finalized_date',
            'finalization_reason', 'evidence_paths', 'write_off_group_id'
        ]

        for col in required_cols:
            assert col in columns, f"Column '{col}' should exist in cases table"

        conn.close()

    def test_financial_years_table_schema(self, test_db_path):
        """Test that the financial_years table has the correct schema."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check financial_years table columns
        cursor.execute("PRAGMA table_info(financial_years)")
        columns = [row[1] for row in cursor.fetchall()]

        required_cols = ['id', 'start_year', 'end_year', 'status', 'active_period']
        for col in required_cols:
            assert col in columns, f"Column '{col}' should exist in financial_years table"

        conn.close()

    def test_responsibilities_table_schema(self, test_db_path):
        """Test that the responsibilities table has the correct schema."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check responsibilities table columns
        cursor.execute("PRAGMA table_info(responsibilities)")
        columns = [row[1] for row in cursor.fetchall()]

        required_cols = ['id', 'name', 'parent_id', 'is_posting_level']
        for col in required_cols:
            assert col in columns, f"Column '{col}' should exist in responsibilities table"

        conn.close()

    def test_foreign_key_constraints(self, test_db_path):
        """Test that foreign key constraints are properly set up."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check foreign key constraints on cases table
        cursor.execute("PRAGMA foreign_key_list(cases)")
        fk_constraints = cursor.fetchall()

        # Should have foreign keys to financial_years and responsibilities
        fk_tables = [row[2] for row in fk_constraints]
        assert 'financial_years' in fk_tables, "Cases table should reference financial_years"
        assert 'responsibilities' in fk_tables, "Cases table should reference responsibilities"

        conn.close()

    def test_sample_data_insertion(self, test_db_path):
        """Test that sample data can be inserted correctly."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check that sample data was inserted
        cursor.execute("SELECT COUNT(*) FROM financial_years")
        fy_count = cursor.fetchone()[0]
        assert fy_count > 0, "Should have sample financial years data"

        cursor.execute("SELECT COUNT(*) FROM responsibilities")
        resp_count = cursor.fetchone()[0]
        assert resp_count > 0, "Should have sample responsibilities data"

        cursor.execute("SELECT COUNT(*) FROM cases")
        cases_count = cursor.fetchone()[0]
        assert cases_count > 0, "Should have sample cases data"

        conn.close()
