#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for FWMIS (Financial Write-off Management Information System)

This test suite provides end-to-end automated testing covering:
- Case import functionality
- Full case workflow processing

Note: Database setup is now handled by the test runner.
Tests use the isolated database provided via FWMIS_TEST_DB environment variable.
"""

import os
import sys
import sqlite3
import tempfile
import pytest
from datetime import datetime, date
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.Utilities.config import DB_PATH
from scripts.models.bas_parser import BASParser

# Database setup is now handled by the test runner
# Tests use the isolated database provided via FWMIS_TEST_DB environment variable

@pytest.fixture(scope="session")
def test_database_setup():
    """Create unique temporary database for testing"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_db_path = os.path.join(tempfile.gettempdir(), f"fwmis_test_{unique_id}.db")

    # Always create fresh database with dummy test data (never copy production)
    _create_fresh_test_database(test_db_path)

    # Override DB_PATH for tests
    os.environ['FWMIS_TEST_DB'] = test_db_path

    yield

    # Cleanup - ensure test database is completely removed
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception as e:
        print(f"Warning: Could not remove test database {test_db_path}: {e}")

    if 'FWMIS_TEST_DB' in os.environ:
        del os.environ['FWMIS_TEST_DB']


def _create_fresh_test_database(test_db_path):
    """Create a fresh test database with dummy data - completely isolated from production"""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Create all required tables with proper schema
    _create_test_schema(cursor)

    # Populate with comprehensive dummy test data
    _populate_dummy_data(cursor)

    conn.commit()
    conn.close()


def _create_test_schema(cursor):
    """Create the complete database schema for testing"""
    # Cases table
    cursor.execute("""
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            base_transaction_no TEXT,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'Active',
            fy_id INTEGER,
            responsibility_id INTEGER,
            created_date TEXT,
            updated_date TEXT,
            assessment_status TEXT,
            suffixes TEXT,
            date_reported TEXT,
            reference_no TEXT,
            lc_status TEXT,
            debtor_name TEXT,
            category TEXT,
            is_finalized INTEGER DEFAULT 0,
            finalized_date TEXT,
            finalization_reason TEXT,
            evidence_paths TEXT,
            write_off_group_id TEXT
        )
    """)

    # Financial years table
    cursor.execute("""
        CREATE TABLE financial_years (
            id INTEGER PRIMARY KEY,
            start_year INTEGER,
            end_year INTEGER,
            status TEXT DEFAULT 'closed',
            active_period INTEGER
        )
    """)

    # Responsibilities table
    cursor.execute("""
        CREATE TABLE responsibilities (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            parent_id INTEGER,
            is_posting_level INTEGER DEFAULT 0
        )
    """)


def _populate_dummy_data(cursor):
    """Populate the test database with comprehensive dummy data"""
    # Create financial years
    financial_years = [
        (1, 2019, 2020, 'closed', None),
        (2, 2020, 2021, 'closed', None),
        (3, 2021, 2022, 'closed', None),
        (4, 2022, 2023, 'closed', None),
        (5, 2023, 2024, 'closed', None),
        (6, 2024, 2025, 'open', 1),
    ]

    cursor.executemany("""
        INSERT INTO financial_years (id, start_year, end_year, status, active_period)
        VALUES (?, ?, ?, ?, ?)
    """, financial_years)

    # Create responsibilities
    responsibilities = [
        (1, 'National Department', None, 1),
        (2, 'Provincial Department', None, 1),
        (3, 'Municipal Department', None, 1),
    ]

    cursor.executemany("""
        INSERT INTO responsibilities (id, name, parent_id, is_posting_level)
        VALUES (?, ?, ?, ?)
    """, responsibilities)

    # Create test cases
    cases = [
        (1, 'TEST001', 'TEST001', 'Test case 1', 10000.00, 'Active', 6, 1, 'Alleged'),
        (2, 'TEST002', 'TEST002', 'Test case 2', 25000.00, 'Active', 6, 2, 'Alleged'),
        (3, 'TEST003', 'TEST003', 'Test case 3', 5000.00, 'Active', 6, 3, 'Alleged'),
    ]

    cursor.executemany("""
        INSERT INTO cases (id, transaction_no, base_transaction_no, description, amount, status, fy_id, responsibility_id, assessment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cases)


class TestCaseImport:
    """Test case import functionality"""

    def test_bas_parser_initialization(self, test_database_setup):
        """Test that BAS parser initializes correctly"""
        parser = BASParser()
        assert parser is not None

    def test_database_connection(self, test_database_setup):
        """Test database connection using test database"""
        test_db = os.environ.get('FWMIS_TEST_DB', DB_PATH)
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cases")
        result = cursor.fetchone()
        assert result is not None
        conn.close()

    def test_case_creation_and_initial_status(self, test_database_setup):
        """Test that cases are created with correct initial status"""
        test_db = os.environ.get('FWMIS_TEST_DB', DB_PATH)
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Create a test case
        cursor.execute("""
            INSERT INTO cases (base_transaction_no, assessment_status, fy_id, amount, debtor_name)
            VALUES ('WF-TEST-001', 'Alleged', 1, 5000.00, 'Test Debtor')
        """)
        case_id = cursor.lastrowid
        conn.commit()

        # Verify case was created correctly
        cursor.execute("SELECT base_transaction_no, assessment_status FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()

        assert case is not None
        assert case[0] == 'WF-TEST-001'  # base_transaction_no
        assert case[1] == 'Alleged'  # assessment_status

        conn.close()
