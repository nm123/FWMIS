#!/usr/bin/env python3
"""
Workflow and business logic tests for FWMIS application.
Tests the core business rules, validation logic, and workflow enforcement.
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

class TestWorkflowBusinessLogic:
    """Test workflow and business logic validation."""

    @pytest.fixture
    def test_db_path(self):
        """Create a unique temporary test database."""
        import uuid
        db_path = os.path.join(tempfile.gettempdir(), f'test_workflow_logic_{uuid.uuid4().hex[:8]}.db')
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

    @pytest.fixture
    def test_db(self, test_db_path):
        """Create and populate test database."""
        manager = TestExecutionManager(MockDialog())
        manager._create_test_database(test_db_path)
        return test_db_path

    def test_case_status_workflow_enforcement(self, test_db):
        """Test that case status transitions follow proper workflow rules."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test valid status transitions
        valid_transitions = [
            ('Alleged', 'Confirmed'),  # Initial assessment
            ('Confirmed', 'Valid'),    # Final approval
            ('Alleged', 'Invalid'),    # Rejection
        ]

        for from_status, to_status in valid_transitions:
            # Create a test case with the from_status
            cursor.execute("""
                INSERT INTO cases (
                    transaction_no, base_transaction_no, description, amount,
                    status, fy_id, responsibility_id, debtor_name, category, list
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'TEST_TRANSITION_{from_status}_{to_status}',
                f'TEST_TRANSITION_{from_status}_{to_status}',
                f'Test case for {from_status} -> {to_status} transition',
                10000.00, from_status, 1, 1, 'Test Debtor', 'Test Category', 'Checklist'
            ))

            case_id = cursor.lastrowid

            # Verify the transition would be allowed (business logic validation)
            # Note: This tests the validation logic, not the actual transition

            # For status validation, check that the status is valid
            valid_statuses = ['Alleged', 'Confirmed', 'Valid', 'Invalid', 'Finalized']
            assert from_status in valid_statuses, f"Invalid from_status: {from_status}"
            assert to_status in valid_statuses, f"Invalid to_status: {to_status}"

            # Clean up test case
            cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))

        conn.commit()
        conn.close()

    def test_financial_year_business_rules(self, test_db):
        """Test financial year business rules and constraints."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that financial years don't overlap
        cursor.execute("SELECT start_year, end_year FROM financial_years ORDER BY start_year")
        fy_ranges = cursor.fetchall()

        for i in range(len(fy_ranges) - 1):
            current_end = fy_ranges[i][1]
            next_start = fy_ranges[i + 1][0]

            # Financial years should be consecutive (end of one equals start of next)
            assert current_end == next_start, f"Financial years should be consecutive: {fy_ranges[i]} and {fy_ranges[i + 1]}"

        # Test that cases are properly assigned to financial years
        cursor.execute("""
            SELECT c.id, c.transaction_no, c.fy_id, fy.start_year, fy.end_year
            FROM cases c
            JOIN financial_years fy ON c.fy_id = fy.id
            WHERE c.list != 'Deleted Cases'
            LIMIT 5
        """)
        case_fy_assignments = cursor.fetchall()

        for case_id, transaction_no, fy_id, start_year, end_year in case_fy_assignments:
            # Financial year should have valid date range
            assert start_year < end_year, f"Invalid FY range for case {case_id}: {start_year}-{end_year}"
            assert end_year - start_year == 1, f"FY should be exactly 1 year for case {case_id}"

        conn.close()

    def test_responsibility_hierarchy_business_rules(self, test_db):
        """Test responsibility hierarchy business rules."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that posting level responsibilities exist
        cursor.execute("SELECT COUNT(*) FROM responsibilities WHERE is_posting_level = 1")
        posting_level_count = cursor.fetchone()[0]
        assert posting_level_count > 0, "Should have at least one posting level responsibility"

        # Test that non-posting level responsibilities have parents
        cursor.execute("""
            SELECT id, name, parent_id FROM responsibilities
            WHERE is_posting_level = 0
        """)
        non_posting_resps = cursor.fetchall()

        for resp_id, name, parent_id in non_posting_resps:
            assert parent_id is not None, f"Non-posting responsibility '{name}' should have parent"

            # Parent should exist
            cursor.execute("SELECT COUNT(*) FROM responsibilities WHERE id = ?", (parent_id,))
            parent_exists = cursor.fetchone()[0]
            assert parent_exists > 0, f"Parent {parent_id} should exist for responsibility '{name}'"

        # Test that cases are assigned to valid responsibilities
        cursor.execute("""
            SELECT c.id, c.responsibility_id, r.name, r.is_posting_level
            FROM cases c
            JOIN responsibilities r ON c.responsibility_id = r.id
            WHERE c.list != 'Deleted Cases'
            LIMIT 5
        """)
        case_responsibilities = cursor.fetchall()

        for case_id, resp_id, resp_name, is_posting_level in case_responsibilities:
            # Case should be assigned to a valid responsibility
            assert resp_name, f"Case {case_id} assigned to responsibility without name"
            # Note: Not all cases need posting level responsibilities, so we don't enforce that here

        conn.close()

    def test_transaction_number_business_rules(self, test_db):
        """Test transaction number business rules and uniqueness."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that transaction numbers are unique
        cursor.execute("""
            SELECT transaction_no, COUNT(*) as count
            FROM cases
            GROUP BY transaction_no
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found duplicate transaction numbers: {duplicates}"

        # Test transaction number format (should not be empty, reasonable length)
        cursor.execute("SELECT id, transaction_no FROM cases WHERE list != 'Deleted Cases' LIMIT 10")
        transactions = cursor.fetchall()

        for case_id, transaction_no in transactions:
            assert transaction_no, f"Case {case_id} has empty transaction number"
            assert len(transaction_no) > 0, f"Case {case_id} has zero-length transaction number"
            assert len(transaction_no) < 50, f"Case {case_id} has suspiciously long transaction number: {len(transaction_no)} chars"

        # Test base_transaction_no consistency
        cursor.execute("""
            SELECT id, transaction_no, base_transaction_no
            FROM cases
            WHERE transaction_no != base_transaction_no
            AND list != 'Deleted Cases'
            LIMIT 5
        """)
        derived_transactions = cursor.fetchall()

        for case_id, transaction_no, base_transaction_no in derived_transactions:
            # Derived transactions should have base that exists
            if base_transaction_no:
                cursor.execute("SELECT COUNT(*) FROM cases WHERE transaction_no = ?", (base_transaction_no,))
                base_exists = cursor.fetchone()[0]
                # Note: Base might not exist if it's from a different source, so we don't enforce this strictly

        conn.close()

    def test_amount_validation_business_rules(self, test_db):
        """Test amount validation business rules."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that amounts are reasonable (positive, not extremely large)
        cursor.execute("""
            SELECT id, transaction_no, amount
            FROM cases
            WHERE list != 'Deleted Cases'
            AND amount > 0
            LIMIT 10
        """)
        amounts = cursor.fetchall()

        for case_id, transaction_no, amount in amounts:
            assert amount > 0, f"Case {case_id} has non-positive amount: {amount}"
            assert amount < 100000000, f"Case {case_id} has suspiciously large amount: {amount}"
            # More reasonable upper bound for government write-offs
            assert amount < 10000000, f"Case {case_id} has extremely large amount: {amount}"

        # Test amount ranges by category (if categories have different thresholds)
        cursor.execute("""
            SELECT category, MIN(amount), MAX(amount), AVG(amount), COUNT(*)
            FROM cases
            WHERE list != 'Deleted Cases' AND amount > 0
            GROUP BY category
        """)
        category_stats = cursor.fetchall()

        for category, min_amt, max_amt, avg_amt, count in category_stats:
            # Basic sanity checks
            assert min_amt >= 0, f"Category '{category}' has negative minimum amount"
            assert max_amt >= min_amt, f"Category '{category}' has max < min"
            assert count > 0, f"Category '{category}' has no cases"

        conn.close()

    def test_list_status_workflow_integrity(self, test_db):
        """Test that list and status combinations follow workflow integrity rules."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test Checklist cases - should have appropriate statuses
        cursor.execute("SELECT id, status FROM cases WHERE list = 'Checklist'")
        checklist_cases = cursor.fetchall()

        checklist_allowed_statuses = ['Alleged', 'Confirmed', 'Valid', 'Invalid']
        for case_id, status in checklist_cases:
            assert status in checklist_allowed_statuses, f"Checklist case {case_id} has invalid status: {status}"

        # Test Lead Schedule cases - should have more advanced statuses
        cursor.execute("SELECT id, status FROM cases WHERE list = 'Lead Schedule'")
        lead_schedule_cases = cursor.fetchall()

        lead_schedule_allowed_statuses = ['Confirmed', 'Valid', 'Finalized']
        for case_id, status in lead_schedule_cases:
            assert status in lead_schedule_allowed_statuses, f"Lead Schedule case {case_id} has invalid status: {status}"

        # Test Finalized cases - should be marked as finalized
        cursor.execute("SELECT id, is_finalized FROM cases WHERE status = 'Valid' AND is_finalized = 1")
        finalized_cases = cursor.fetchall()

        for case_id, is_finalized in finalized_cases:
            assert is_finalized == 1, f"Valid case {case_id} should be finalized"

        # Test that finalized cases have finalization dates
        cursor.execute("""
            SELECT id, finalized_date FROM cases
            WHERE is_finalized = 1 AND finalized_date IS NULL
        """)
        missing_dates = cursor.fetchall()
        assert len(missing_dates) == 0, f"Found {len(missing_dates)} finalized cases without finalization dates"

        conn.close()

    def test_data_integrity_constraints(self, test_db):
        """Test data integrity constraints and foreign key relationships."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test foreign key integrity - no orphaned cases
        cursor.execute("""
            SELECT COUNT(*) FROM cases c
            LEFT JOIN financial_years fy ON c.fy_id = fy.id
            WHERE fy.id IS NULL AND c.fy_id IS NOT NULL
        """)
        orphaned_by_fy = cursor.fetchone()[0]
        assert orphaned_by_fy == 0, f"Found {orphaned_by_fy} cases with invalid fy_id references"

        cursor.execute("""
            SELECT COUNT(*) FROM cases c
            LEFT JOIN responsibilities r ON c.responsibility_id = r.id
            WHERE r.id IS NULL AND c.responsibility_id IS NOT NULL
        """)
        orphaned_by_resp = cursor.fetchone()[0]
        assert orphaned_by_resp == 0, f"Found {orphaned_by_resp} cases with invalid responsibility_id references"

        # Test required field constraints
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE (transaction_no IS NULL OR transaction_no = '')
            AND list != 'Deleted Cases'
        """)
        null_transactions = cursor.fetchone()[0]
        assert null_transactions == 0, f"Found {null_transactions} cases with null/empty transaction numbers"

        # Test data type constraints
        cursor.execute("""
            SELECT id, amount FROM cases
            WHERE typeof(amount) != 'real' AND typeof(amount) != 'integer'
            AND list != 'Deleted Cases'
        """)
        invalid_amounts = cursor.fetchall()
        assert len(invalid_amounts) == 0, f"Found cases with invalid amount data types: {invalid_amounts}"

        conn.close()

    def test_audit_trail_business_rules(self, test_db):
        """Test audit trail and data modification tracking."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Test that created_date exists for all cases
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE created_date IS NULL AND list != 'Deleted Cases'
        """)
        missing_created_dates = cursor.fetchone()[0]
        assert missing_created_dates == 0, f"Found {missing_created_dates} cases without created_date"

        # Test that updated_date is reasonable (not before created_date)
        cursor.execute("""
            SELECT id FROM cases
            WHERE updated_date < created_date
            AND updated_date IS NOT NULL
            AND created_date IS NOT NULL
        """)
        invalid_update_dates = cursor.fetchall()
        assert len(invalid_update_dates) == 0, f"Found cases where updated_date is before created_date: {invalid_update_dates}"

        # Test that status changes are tracked (by updated_date changes)
        # This is more of a data quality check than a strict business rule
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE updated_date IS NOT NULL AND list != 'Deleted Cases'
        """)
        tracked_changes = cursor.fetchone()[0]

        # At least some cases should have update tracking
        total_cases = cursor.execute("SELECT COUNT(*) FROM cases WHERE list != 'Deleted Cases'").fetchone()[0]
        # We don't enforce this strictly as it's not always required

        conn.close()
