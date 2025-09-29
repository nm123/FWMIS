"""
Unit tests for AnnexureRepository.
"""

import pytest
from datetime import datetime


class TestAnnexureRepository:
    """Test cases for AnnexureRepository functionality."""

    def test_get_annexure_by_id(self, annexure_repository, in_memory_db):
        """Test retrieving an annexure by ID."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no, status, created_date)
            VALUES (1, 'ANNEX001', 'Draft', '2024-01-01T10:00:00')
        """)
        in_memory_db.commit()

        # Test retrieval
        annexure = annexure_repository.get_annexure_by_id(1)

        assert annexure is not None
        assert annexure["id"] == 1
        assert annexure["annexure_no"] == "ANNEX001"
        assert annexure["status"] == "Draft"

    def test_get_annexure_by_id_not_found(self, annexure_repository):
        """Test retrieving a non-existent annexure."""
        annexure = annexure_repository.get_annexure_by_id(999)
        assert annexure is None

    def test_get_annexures_by_status(self, annexure_repository, in_memory_db):
        """Test retrieving annexures by status."""
        # Setup test data
        test_annexures = [
            (1, "ANNEX001", "Draft"),
            (2, "ANNEX002", "Draft"),
            (3, "ANNEX003", "Approved"),
            (4, "ANNEX004", "Rejected")
        ]

        for annex_id, annex_no, status in test_annexures:
            in_memory_db.execute("""
                INSERT INTO write_off_annexures (id, annexure_no, status)
                VALUES (?, ?, ?)
            """, (annex_id, annex_no, status))

        in_memory_db.commit()

        # Test retrieval
        draft_annexures = annexure_repository.get_annexures_by_status("Draft")
        assert len(draft_annexures) == 2
        assert all(annexure["status"] == "Draft" for annexure in draft_annexures)

        approved_annexures = annexure_repository.get_annexures_by_status("Approved")
        assert len(approved_annexures) == 1
        assert approved_annexures[0]["status"] == "Approved"

    def test_create_annexure(self, annexure_repository):
        """Test creating a new annexure."""
        annexure_data = {
            "annexure_no": "CREATE001",
            "status": "Draft",
            "role": "CFO"
        }

        annexure_id = annexure_repository.create_annexure(annexure_data)

        assert annexure_id is not None
        assert isinstance(annexure_id, int)

        # Verify creation
        created_annexure = annexure_repository.get_annexure_by_id(annexure_id)
        assert created_annexure is not None
        assert created_annexure["annexure_no"] == "CREATE001"
        assert created_annexure["status"] == "Draft"

    def test_update_annexure(self, annexure_repository, in_memory_db):
        """Test updating an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no, status)
            VALUES (1, 'UPDATE001', 'Draft')
        """)
        in_memory_db.commit()

        # Update annexure
        updates = {
            "status": "Approved",
            "role": "HOD"
        }
        success = annexure_repository.update_annexure(1, updates)

        assert success

        # Verify update
        updated_annexure = annexure_repository.get_annexure_by_id(1)
        assert updated_annexure["status"] == "Approved"
        assert updated_annexure["role"] == "HOD"
        assert "updated_date" in updated_annexure

    def test_update_annexure_status(self, annexure_repository, in_memory_db):
        """Test updating annexure status."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no, status)
            VALUES (1, 'STATUS001', 'Draft')
        """)
        in_memory_db.commit()

        # Update status
        success = annexure_repository.update_annexure_status(1, "Approved")

        assert success

        # Verify update
        updated_annexure = annexure_repository.get_annexure_by_id(1)
        assert updated_annexure["status"] == "Approved"
        assert "updated_date" in updated_annexure

    def test_update_annexure_status_with_reason(self, annexure_repository, in_memory_db):
        """Test updating annexure status with decline reason."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no, status)
            VALUES (1, 'REASON001', 'Draft')
        """)
        in_memory_db.commit()

        # Update status with reason
        success = annexure_repository.update_annexure_status(1, "Declined", "Insufficient documentation")

        assert success

        # Verify update
        updated_annexure = annexure_repository.get_annexure_by_id(1)
        assert updated_annexure["status"] == "Declined"
        assert updated_annexure["decline_reason"] == "Insufficient documentation"

    def test_delete_annexure(self, annexure_repository, in_memory_db):
        """Test deleting an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no, status)
            VALUES (1, 'DELETE001', 'Draft')
        """)
        in_memory_db.commit()

        # Delete annexure
        success = annexure_repository.delete_annexure(1)
        assert success

        # Verify deletion
        deleted_annexure = annexure_repository.get_annexure_by_id(1)
        assert deleted_annexure is None

    def test_add_cases_to_annexure(self, annexure_repository, in_memory_db):
        """Test adding cases to an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no)
            VALUES (1, 'ADD001')
        """)

        # Create test cases first
        case_ids = [1, 2, 3]
        for case_id in case_ids:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, description)
                VALUES (?, ?, ?)
            """, (case_id, f"CASE{case_id:03d}", f"Test case {case_id}"))

        in_memory_db.commit()

        # Add some cases
        added_count = annexure_repository.add_cases_to_annexure(1, case_ids)

        assert added_count == 3

        # Verify cases were added
        annexure_cases = annexure_repository.get_annexure_cases(1)
        assert len(annexure_cases) == 3
        assert {case["id"] for case in annexure_cases} == set(case_ids)

    def test_remove_cases_from_annexure(self, annexure_repository, in_memory_db):
        """Test removing cases from an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no)
            VALUES (1, 'REMOVE001')
        """)

        # Create test cases first
        case_ids = [1, 2, 3, 4, 5]
        for case_id in case_ids:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, description)
                VALUES (?, ?, ?)
            """, (case_id, f"CASE{case_id:03d}", f"Test case {case_id}"))

        in_memory_db.commit()

        # Add cases first
        annexure_repository.add_cases_to_annexure(1, case_ids)

        # Remove some cases
        remove_ids = [2, 4]
        removed_count = annexure_repository.remove_cases_from_annexure(1, remove_ids)

        assert removed_count == 2

        # Verify remaining cases
        remaining_cases = annexure_repository.get_annexure_cases(1)
        remaining_ids = {case["id"] for case in remaining_cases}
        assert remaining_ids == {1, 3, 5}

    def test_get_annexure_cases(self, annexure_repository, in_memory_db):
        """Test retrieving cases for an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no)
            VALUES (1, 'CASES001')
        """)

        # Add cases with different transaction numbers
        cases_data = [
            (1, "TRANS001"),
            (2, "TRANS002"),
            (3, "TRANS003")
        ]

        for case_id, trans_no in cases_data:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no)
                VALUES (?, ?)
            """, (case_id, trans_no))

        annexure_repository.add_cases_to_annexure(1, [1, 2, 3])

        # Get annexure cases
        annexure_cases = annexure_repository.get_annexure_cases(1)

        assert len(annexure_cases) == 3
        trans_nos = [case["transaction_no"] for case in annexure_cases]
        assert set(trans_nos) == {"TRANS001", "TRANS002", "TRANS003"}

    def test_update_associated_case_statuses(self, annexure_repository, in_memory_db):
        """Test updating status of all cases associated with an annexure."""
        # Setup test data
        in_memory_db.execute("""
            INSERT INTO write_off_annexures (id, annexure_no)
            VALUES (1, 'STATUS001')
        """)

        # Add cases
        cases_data = [
            (1, "CASE001", "Active"),
            (2, "CASE002", "Active"),
            (3, "CASE003", "Draft")
        ]

        for case_id, trans_no, status in cases_data:
            in_memory_db.execute("""
                INSERT INTO cases (id, transaction_no, description, status, lc_status)
                VALUES (?, ?, ?, ?, ?)
            """, (case_id, trans_no, f"Test case {case_id}", status, "Pending"))

        annexure_repository.add_cases_to_annexure(1, [1, 2, 3])

        # Update associated case statuses
        updated_count = annexure_repository.update_associated_case_statuses(
            1, "Write Off Recommended", "Write Off Recommended"
        )

        assert updated_count == 3

        # Verify all associated cases were updated
        annexure_cases = annexure_repository.get_annexure_cases(1)
        for case in annexure_cases:
            assert case["status"] == "Write Off Recommended"
            assert case["lc_status"] == "Write Off Recommended"
