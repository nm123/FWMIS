"""
Annexure Repository

Data access layer for annexure-related database operations following the Repository pattern.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from scripts.Utilities.database_connection import DatabaseManager
from scripts.Utilities.sql_builder import SQLBuilder

logger = logging.getLogger(__name__)


class AnnexureRepository:
    """Repository for annexure-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_annexure_by_id(self, annexure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an annexure by ID.

        Args:
            annexure_id: The annexure ID

        Returns:
            Annexure data as dictionary or None if not found
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "write_off_annexures", where_conditions={"id": annexure_id}
            )
            results = self.db_manager.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get annexure {annexure_id}: {e}")
            return None

    def get_annexures_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get annexures by status.

        Args:
            status: Annexure status to filter by

        Returns:
            List of annexure dictionaries
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "write_off_annexures",
                where_conditions={"status": status},
                order_by="created_date DESC",
            )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get annexures by status '{status}': {e}")
            return []

    def get_annexure_with_details(self, annexure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get annexure with case count and total amount.

        Args:
            annexure_id: The annexure ID

        Returns:
            Annexure data with additional computed fields
        """
        try:
            query = """
                SELECT
                    a.*,
                    COUNT(ac.case_id) as cases_count,
                    COALESCE(SUM(c.amount), 0) as total_amount
                FROM write_off_annexures a
                LEFT JOIN write_off_annexure_cases ac ON a.id = ac.annexure_id
                LEFT JOIN cases c ON ac.case_id = c.id
                WHERE a.id = ?
                GROUP BY a.id
            """
            results = self.db_manager.execute_query(query, [annexure_id])
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get annexure details for {annexure_id}: {e}")
            return None

    def get_all_annexures_with_details(self) -> List[Dict[str, Any]]:
        """
        Get all annexures with case counts and total amounts.

        Returns:
            List of annexure dictionaries with computed fields
        """
        try:
            query = """
                SELECT
                    a.*,
                    COUNT(ac.case_id) as cases_count,
                    COALESCE(SUM(c.amount), 0) as total_amount
                FROM write_off_annexures a
                LEFT JOIN write_off_annexure_cases ac ON a.id = ac.annexure_id
                LEFT JOIN cases c ON ac.case_id = c.id
                GROUP BY a.id
                ORDER BY a.created_date DESC
            """
            return self.db_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get all annexures with details: {e}")
            return []

    def create_annexure(self, annexure_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new annexure.

        Args:
            annexure_data: Annexure data dictionary

        Returns:
            New annexure ID if successful, None otherwise
        """
        try:
            # Add created_date if not provided
            if "created_date" not in annexure_data:
                annexure_data["created_date"] = datetime.now().isoformat()

            query, params = SQLBuilder.build_insert_query(
                "write_off_annexures", annexure_data
            )
            self.db_manager.execute_update(query, params)

            # Get the last inserted row ID
            result = self.db_manager.execute_query("SELECT last_insert_rowid() as id")
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Failed to create annexure: {e}")
            return None

    def update_annexure(self, annexure_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an annexure with the provided data.

        Args:
            annexure_id: The annexure ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add updated_date if not provided
            if "updated_date" not in updates:
                updates["updated_date"] = datetime.now().isoformat()

            query, params = SQLBuilder.build_update_query(
                "write_off_annexures", updates, "id = ?", [annexure_id]
            )
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to update annexure {annexure_id}: {e}")
            return False

    def update_annexure_status(
        self, annexure_id: int, status: str, decline_reason: Optional[str] = None
    ) -> bool:
        """
        Update annexure status with optional decline reason.

        Args:
            annexure_id: The annexure ID
            status: New status
            decline_reason: Optional decline reason

        Returns:
            True if successful, False otherwise
        """
        updates = {"status": status, "updated_date": datetime.now().isoformat()}
        if decline_reason is not None:
            updates["decline_reason"] = decline_reason

        return self.update_annexure(annexure_id, updates)

    def delete_annexure(self, annexure_id: int) -> bool:
        """
        Delete an annexure and its associated case relationships.

        Args:
            annexure_id: The annexure ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.transaction() as conn:
                cursor = conn.cursor()

                # Delete annexure-case relationships first
                cursor.execute(
                    "DELETE FROM write_off_annexure_cases WHERE annexure_id = ?",
                    (annexure_id,),
                )

                # Delete annexure
                cursor.execute(
                    "DELETE FROM write_off_annexures WHERE id = ?", (annexure_id,)
                )

            return True
        except Exception as e:
            logger.error(f"Failed to delete annexure {annexure_id}: {e}")
            return False

    def add_cases_to_annexure(self, annexure_id: int, case_ids: List[int]) -> int:
        """
        Add cases to an annexure.

        Args:
            annexure_id: The annexure ID
            case_ids: List of case IDs to add

        Returns:
            Number of cases successfully added
        """
        try:
            added_count = 0
            with self.db_manager.transaction() as conn:
                cursor = conn.cursor()

                for case_id in case_ids:
                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO write_off_annexure_cases
                            (annexure_id, case_id, added_date)
                            VALUES (?, ?, ?)
                        """,
                            (annexure_id, case_id, datetime.now().isoformat()),
                        )
                        added_count += cursor.rowcount
                    except Exception as e:
                        logger.warning(
                            f"Failed to add case {case_id} to annexure {annexure_id}: {e}"
                        )

            return added_count
        except Exception as e:
            logger.error(f"Failed to add cases to annexure {annexure_id}: {e}")
            return 0

    def remove_cases_from_annexure(self, annexure_id: int, case_ids: List[int]) -> int:
        """
        Remove cases from an annexure.

        Args:
            annexure_id: The annexure ID
            case_ids: List of case IDs to remove

        Returns:
            Number of cases successfully removed
        """
        try:
            if not case_ids:
                return 0

            placeholders = ", ".join("?" * len(case_ids))
            query = f"""
                DELETE FROM write_off_annexure_cases
                WHERE annexure_id = ? AND case_id IN ({placeholders})
            """
            params = [annexure_id] + case_ids

            return self.db_manager.execute_update(query, params)
        except Exception as e:
            logger.error(f"Failed to remove cases from annexure {annexure_id}: {e}")
            return 0

    def get_annexure_cases(self, annexure_id: int) -> List[Dict[str, Any]]:
        """
        Get all cases associated with an annexure.

        Args:
            annexure_id: The annexure ID

        Returns:
            List of case dictionaries
        """
        try:
            query = """
                SELECT c.*
                FROM cases c
                INNER JOIN write_off_annexure_cases ac ON c.id = ac.case_id
                WHERE ac.annexure_id = ?
                ORDER BY c.transaction_no
            """
            return self.db_manager.execute_query(query, [annexure_id])
        except Exception as e:
            logger.error(f"Failed to get cases for annexure {annexure_id}: {e}")
            return []

    def update_associated_case_statuses(
        self, annexure_id: int, status: str, lc_status: Optional[str] = None
    ) -> int:
        """
        Update status of all cases associated with an annexure.

        Args:
            annexure_id: The annexure ID
            status: New case status
            lc_status: New LC status (optional)

        Returns:
            Number of cases updated
        """
        try:
            updates = {"status": status}
            if lc_status:
                updates["lc_status"] = lc_status

            query, params = SQLBuilder.build_update_query(
                "cases",
                updates,
                "id IN (SELECT case_id FROM write_off_annexure_cases WHERE annexure_id = ?)",
                [annexure_id],
            )
            return self.db_manager.execute_update(query, params)
        except Exception as e:
            logger.error(
                f"Failed to update associated case statuses for annexure {annexure_id}: {e}"
            )
            return 0

    def get_all_annexures(self) -> List[Dict[str, Any]]:
        """
        Get all annexures without additional computed fields.

        Returns:
            List of annexure dictionaries
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "write_off_annexures",
                order_by="created_date DESC",
            )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get all annexures: {e}")
            return []

    def count_pending_annexures(self) -> int:
        """
        Count annexures with pending status.

        Returns:
            Number of pending annexures
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM write_off_annexures
                WHERE status = 'pending' OR status = 'Pending'
            """
            results = self.db_manager.execute_query(query)
            return results[0]["count"] if results else 0
        except Exception as e:
            logger.error(f"Failed to count pending annexures: {e}")
            return 0
