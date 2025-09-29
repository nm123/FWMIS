"""
Unit tests for CaseRepository.
"""

import pytest
from datetime import datetime


class TestCaseRepository:
    """Test cases for CaseRepository functionality."""

    def test_get_case_by_id(self, case_repository, in_memory_db):
        """Test retrieving a case by ID."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO cases (id, transaction_no, description, amount, status)
            VALUES (1, 'TEST001', 'Test Case', 1000.50, 'Active')
        """)
        in_memory_db.commit()

        # Test retrieval
        case = case_repository.get_case_by_id(1)

        assert case is not None
        assert case["id"] == 1
        assert case["transaction_no"] == "TEST001"
        assert case["description"] == "Test Case"
        assert case["amount"] == 1000.50
        assert case["status"] == "Active"

    def test_get_case_by_id_not_found(self, case_repository):
        """Test retrieving a non-existent case."""
        case = case_repository.get_case_by_id(999)
        assert case is None

    def test_get_case_by_transaction_no(self, case_repository, in_memory_db):
        """Test retrieving a case by transaction number."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO cases (transaction_no, description, amount)
            VALUES ('TRANS001', 'Transaction Test', 2500.00)
        """)
        in_memory_db.commit()

        # Test retrieval
        case = case_repository.get_case_by_transaction_no("TRANS001")

        assert case is not None
        assert case["transaction_no"] == "TRANS001"
        assert case["description"] == "Transaction Test"

    def test_update_case(self, case_repository, in_memory_db):
        """Test updating a case."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO cases (id, transaction_no, description, amount, status)
            VALUES (1, 'UPDATE001', 'Original Description', 1000.00, 'Active')
        """)
        in_memory_db.commit()

        # Update case
        updates = {
            "description": "Updated Description",
            "amount": 1500.00,
            "status": "Approved"
        }
        success = case_repository.update_case(1, updates)

        assert success

        # Verify update
        updated_case = case_repository.get_case_by_id(1)
        assert updated_case["description"] == "Updated Description"
        assert updated_case["amount"] == 1500.00
        assert updated_case["status"] == "Approved"
        assert "updated_date" in updated_case

    def test_update_case_not_found(self, case_repository):
        """Test updating a non-existent case."""
        success = case_repository.update_case(999, {"status": "Approved"})
        assert not success

    def test_create_case(self, case_repository):
        """Test creating a new case."""
        case_data = {
            "transaction_no": "CREATE001",
            "description": "Created Case",
            "amount": 3000.00,
            "status": "Draft",
            "fy_id": 1,
            "responsibility_id": 1
        }

        case_id = case_repository.create_case(case_data)

        assert case_id is not None
        assert isinstance(case_id, int)

        # Verify creation
        created_case = case_repository.get_case_by_id(case_id)
        assert created_case is not None
        assert created_case["transaction_no"] == "CREATE001"
        assert created_case["description"] == "Created Case"

    def test_delete_case(self, case_repository, in_memory_db):
        """Test deleting a case."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO cases (id, transaction_no, description)
            VALUES (1, 'DELETE001', 'To Be Deleted')
        """)
        in_memory_db.commit()

        # Delete case
        success = case_repository.delete_case(1)
        assert success

        # Verify deletion
        deleted_case = case_repository.get_case_by_id(1)
        assert deleted_case is None

    def test_delete_case_not_found(self, case_repository):
        """Test deleting a non-existent case."""
        success = case_repository.delete_case(999)
        assert not success

    def test_get_cases_by_status(self, case_repository, in_memory_db):
        """Test retrieving cases by status."""
        # Setup test data
        test_cases = [
            (1, "CASE001", "Active"),
            (2, "CASE002", "Active"),
            (3, "CASE003", "Approved"),
            (4, "CASE004", "Rejected")
        ]

        for case_id, trans_no, status in test_cases:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, status)
                VALUES (?, ?, ?)
            """, (case_id, trans_no, status))

        in_memory_db.commit()

        # Test retrieval
        active_cases = case_repository.get_cases_by_status("Active")
        assert len(active_cases) == 2
        assert all(case["status"] == "Active" for case in active_cases)

        approved_cases = case_repository.get_cases_by_status("Approved")
        assert len(approved_cases) == 1
        assert approved_cases[0]["status"] == "Approved"

    def test_get_case_count_by_status(self, case_repository, in_memory_db):
        """Test getting case counts grouped by status."""
        # Setup test data
        statuses = ["Active", "Active", "Approved", "Rejected", "Active"]
        for i, status in enumerate(statuses, 1):
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, status)
                VALUES (?, ?, ?)
            """, (i, f"CASE{i:03d}", status))

        in_memory_db.commit()

        # Test count
        counts = case_repository.get_case_count_by_status()

        assert counts["Active"] == 3
        assert counts["Approved"] == 1
        assert counts["Rejected"] == 1

    def test_search_cases(self, case_repository, in_memory_db):
        """Test searching cases with various filters."""
        # Setup test data
        test_cases = [
            (1, "SEARCH001", "First case description", "Active", 1),
            (2, "SEARCH002", "Second case description", "Approved", 1),
            (3, "OTHER001", "Different description", "Active", 2)
        ]

        for case_id, trans_no, desc, status, fy_id in test_cases:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, description, status, fy_id)
                VALUES (?, ?, ?, ?, ?)
            """, (case_id, trans_no, desc, status, fy_id))

        in_memory_db.commit()

        # Test search by term
        results = case_repository.search_cases(search_term="SEARCH")
        assert len(results) == 2
        assert all("SEARCH" in case["transaction_no"] for case in results)

        # Test search by status
        results = case_repository.search_cases(status="Active")
        assert len(results) == 2
        assert all(case["status"] == "Active" for case in results)

        # Test search by FY
        results = case_repository.search_cases(fy_id=1)
        assert len(results) == 2
        assert all(case["fy_id"] == 1 for case in results)

    def test_bulk_update_status(self, case_repository, in_memory_db):
        """Test bulk updating status for multiple cases."""
        # Setup test data
        for i in range(1, 6):
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, status)
                VALUES (?, ?, 'Active')
            """, (i, f"BULK{i:03d}"))

        in_memory_db.commit()

        # Bulk update
        case_ids = [1, 3, 5]
        updated_count = case_repository.bulk_update_status(case_ids, "Approved")

        assert updated_count == 3

        # Verify updates
        for case_id in case_ids:
            case = case_repository.get_case_by_id(case_id)
            assert case["status"] == "Approved"

        # Verify non-updated cases
        for case_id in [2, 4]:
            case = case_repository.get_case_by_id(case_id)
            assert case["status"] == "Active"
