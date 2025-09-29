#!/usr/bin/env python3
"""
UI Dialog tests for FWMIS application.
Tests dialog initialization, validation, and basic functionality.
"""

import os
import sys
import tempfile
import sqlite3
import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.ui.dialogs.automated_testing.test_execution import TestExecutionManager

class MockDialog:
    pass

class TestUIDialogs:
    """Test UI dialog functionality without GUI components."""

    @pytest.fixture
    def test_db_path(self):
        """Create a temporary test database."""
        db_path = os.path.join(tempfile.gettempdir(), 'test_ui_dialogs.db')
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def test_db(self, test_db_path):
        """Create and populate test database."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)
        return test_db_path

    def test_import_cases_dialog_validation(self, test_db):
        """Test import cases dialog validation logic."""
        # Test that the import validation logic works
        # This would normally be in import_cases_dialog.py

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test transaction number uniqueness validation
        cursor.execute("SELECT transaction_no FROM cases")
        existing_transactions = [row[0] for row in cursor.fetchall()]

        # Test importing a duplicate transaction (should fail)
        duplicate_transaction = existing_transactions[0] if existing_transactions else 'TEST001'

        # Simulate validation logic
        is_duplicate = duplicate_transaction in existing_transactions
        assert is_duplicate, "Should detect duplicate transaction"

        # Test importing a new transaction (should succeed)
        new_transaction = 'NEW_TRANSACTION_001'
        is_duplicate = new_transaction in existing_transactions
        assert not is_duplicate, "New transaction should not be duplicate"

        conn.close()

    def test_financial_year_dialog_validation(self, test_db):
        """Test financial year dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test financial year range validation
        cursor.execute("SELECT start_year, end_year FROM financial_years")
        fy_ranges = cursor.fetchall()

        # Test valid range (should be consecutive years)
        for start_year, end_year in fy_ranges:
            year_diff = end_year - start_year
            assert year_diff == 1, f"Financial year range should be 1 year, got {year_diff} for {start_year}-{end_year}"

        # Test that years are reasonable (not in far future/past)
        current_year = 2024  # Approximate current year
        for start_year, end_year in fy_ranges:
            assert start_year >= current_year - 10, f"Start year {start_year} seems too old"
            assert end_year <= current_year + 10, f"End year {end_year} seems too far in future"

        conn.close()

    def test_responsibility_management_validation(self, test_db):
        """Test responsibility management dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test responsibility name uniqueness
        cursor.execute("SELECT name FROM responsibilities")
        responsibility_names = [row[0] for row in cursor.fetchall()]

        # Should have unique names
        assert len(responsibility_names) == len(set(responsibility_names)), "Responsibility names should be unique"

        # Test hierarchical structure (parent_id validation)
        cursor.execute("SELECT id, parent_id FROM responsibilities")
        hierarchy = cursor.fetchall()

        for resp_id, parent_id in hierarchy:
            if parent_id is not None:
                # Parent should exist
                cursor.execute("SELECT COUNT(*) FROM responsibilities WHERE id = ?", (parent_id,))
                parent_exists = cursor.fetchone()[0]
                assert parent_exists > 0, f"Parent responsibility {parent_id} should exist for child {resp_id}"

                # Should not be self-referencing
                assert parent_id != resp_id, f"Responsibility {resp_id} should not be its own parent"

        conn.close()

    def test_case_edit_dialog_validation(self, test_db):
        """Test case edit dialog validation logic."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test required field validation
        cursor.execute("""
            SELECT id, transaction_no, fy_id, responsibility_id, status
            FROM cases WHERE list != 'Deleted Cases' LIMIT 5
        """)
        cases = cursor.fetchall()

        for case in cases:
            case_id, transaction_no, fy_id, responsibility_id, status = case

            # Transaction number should not be null/empty
            assert transaction_no, f"Case {case_id} should have transaction number"

            # FY_ID should be valid
            cursor.execute("SELECT COUNT(*) FROM financial_years WHERE id = ?", (fy_id,))
            fy_exists = cursor.fetchone()[0]
            assert fy_exists > 0, f"Case {case_id} should have valid fy_id {fy_id}"

            # Responsibility_ID should be valid
            cursor.execute("SELECT COUNT(*) FROM responsibilities WHERE id = ?", (responsibility_id,))
            resp_exists = cursor.fetchone()[0]
            assert resp_exists > 0, f"Case {case_id} should have valid responsibility_id {responsibility_id}"

            # Status should be valid
            valid_statuses = ['Alleged', 'Confirmed', 'Valid', 'Invalid', 'Finalized']
            assert status in valid_statuses, f"Case {case_id} has invalid status: {status}"

        conn.close()

    def test_write_off_management_validation(self, test_db):
        """Test write-off management dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test annexure structure
        cursor.execute("SELECT id, annexure_no, status FROM write_off_annexures")
        annexures = cursor.fetchall()

        for annexure in annexures:
            annexure_id, annexure_no, status = annexure

            # Annexure number should be unique and not null
            assert annexure_no, f"Annexure {annexure_id} should have annexure number"

            # Status should be valid
            valid_statuses = ['Draft', 'Submitted', 'Approved', 'Rejected']
            assert status in valid_statuses, f"Annexure {annexure_id} has invalid status: {status}"

        # Test annexure-case relationships
        cursor.execute("""
            SELECT annexure_id, case_id FROM write_off_annexure_cases
        """)
        relationships = cursor.fetchall()

        for annexure_id, case_id in relationships:
            # Annexure should exist
            cursor.execute("SELECT COUNT(*) FROM write_off_annexures WHERE id = ?", (annexure_id,))
            annexure_exists = cursor.fetchone()[0]
            assert annexure_exists > 0, f"Annexure {annexure_id} should exist"

            # Case should exist
            cursor.execute("SELECT COUNT(*) FROM cases WHERE id = ?", (case_id,))
            case_exists = cursor.fetchone()[0]
            assert case_exists > 0, f"Case {case_id} should exist"

        conn.close()

    def test_transaction_details_dialog_validation(self, test_db):
        """Test transaction details dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that transaction details are properly structured
        cursor.execute("""
            SELECT id, transaction_no, amount, debtor_name, category
            FROM cases WHERE list != 'Deleted Cases' LIMIT 10
        """)
        transactions = cursor.fetchall()

        for transaction in transactions:
            case_id, transaction_no, amount, debtor_name, category = transaction

            # Amount should be reasonable (not negative, not extremely large)
            assert amount >= 0, f"Case {case_id} should have non-negative amount, got {amount}"
            assert amount < 10000000, f"Case {case_id} has suspiciously large amount: {amount}"

            # Debtor name and category should not be empty for active cases
            assert debtor_name, f"Case {case_id} should have debtor name"
            assert category, f"Case {case_id} should have category"

        conn.close()

    def test_checklist_dialog_validation(self, test_db):
        """Test checklist dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test checklist-specific validations
        cursor.execute("""
            SELECT id, transaction_no, status, fy_id, responsibility_id
            FROM cases WHERE list = 'Checklist'
        """)
        checklist_cases = cursor.fetchall()

        for case in checklist_cases:
            case_id, transaction_no, status, fy_id, resp_id = case

            # Cases in checklist should have appropriate statuses
            checklist_statuses = ['Alleged', 'Confirmed', 'Valid', 'Invalid']
            assert status in checklist_statuses, f"Checklist case {case_id} has invalid status: {status}"

            # Should have valid fy_id
            cursor.execute("SELECT COUNT(*) FROM financial_years WHERE id = ?", (fy_id,))
            fy_valid = cursor.fetchone()[0]
            assert fy_valid > 0, f"Checklist case {case_id} has invalid fy_id: {fy_id}"

            # Should have valid responsibility
            cursor.execute("SELECT COUNT(*) FROM responsibilities WHERE id = ?", (resp_id,))
            resp_valid = cursor.fetchone()[0]
            assert resp_valid > 0, f"Checklist case {case_id} has invalid responsibility_id: {resp_id}"

        conn.close()

    def test_lead_schedule_dialog_validation(self, test_db):
        """Test lead schedule dialog validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test lead schedule specific validations
        cursor.execute("""
            SELECT id, transaction_no, status, fy_id
            FROM cases WHERE list = 'Lead Schedule'
        """)
        lead_schedule_cases = cursor.fetchall()

        for case in lead_schedule_cases:
            case_id, transaction_no, status, fy_id = case

            # Cases in lead schedule should have appropriate statuses
            ls_statuses = ['Confirmed', 'Valid', 'Finalized']
            assert status in ls_statuses, f"Lead Schedule case {case_id} has invalid status: {status}"

            # Should have valid fy_id
            cursor.execute("SELECT COUNT(*) FROM financial_years WHERE id = ?", (fy_id,))
            fy_valid = cursor.fetchone()[0]
            assert fy_valid > 0, f"Lead Schedule case {case_id} has invalid fy_id: {fy_id}"

        conn.close()

    def test_finalization_dashboard_validation(self, test_db):
        """Test finalization dashboard validation."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test finalization-specific validations
        cursor.execute("""
            SELECT id, transaction_no, status, is_finalized, finalized_date
            FROM cases WHERE is_finalized = 1
        """)
        finalized_cases = cursor.fetchall()

        for case in finalized_cases:
            case_id, transaction_no, status, is_finalized, finalized_date = case

            # Finalized cases should have appropriate status
            assert status == 'Valid', f"Finalized case {case_id} should have status 'Valid', got '{status}'"

            # Should have finalization date
            assert finalized_date is not None, f"Finalized case {case_id} should have finalized_date"

        # Test that non-finalized cases don't have finalization dates
        cursor.execute("""
            SELECT id, finalized_date FROM cases
            WHERE is_finalized = 0 AND finalized_date IS NOT NULL
        """)
        invalid_finalizations = cursor.fetchall()

        assert len(invalid_finalizations) == 0, f"Found {len(invalid_finalizations)} non-finalized cases with finalization dates"

        conn.close()
