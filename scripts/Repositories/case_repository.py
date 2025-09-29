"""
Case Repository

Data access layer for case-related database operations following the Repository pattern.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from scripts.Utilities.database_connection import DatabaseManager
from scripts.Utilities.sql_builder import SQLBuilder

logger = logging.getLogger(__name__)


class CaseRepository:
    """Repository for case-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_case_by_id(self, case_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a case by ID.

        Args:
            case_id: The case ID

        Returns:
            Case data as dictionary or None if not found
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "cases", where_conditions={"id": case_id}
            )
            results = self.db_manager.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get case {case_id}: {e}")
            return None

    def get_case_by_transaction_no(
        self, transaction_no: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a case by transaction number.

        Args:
            transaction_no: The transaction number

        Returns:
            Case data as dictionary or None if not found
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "cases", where_conditions={"transaction_no": transaction_no}
            )
            results = self.db_manager.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get case by transaction_no {transaction_no}: {e}")
            return None

    def get_cases_by_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cases by status.

        Args:
            status: Case status to filter by
            limit: Maximum number of results

        Returns:
            List of case dictionaries
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "cases",
                where_conditions={"status": status},
                order_by="date_reported DESC",
                limit=limit,
            )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get cases by status '{status}': {e}")
            return []

    def get_cases_by_responsibility(
        self, responsibility_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get cases by responsibility ID.

        Args:
            responsibility_id: The responsibility ID

        Returns:
            List of case dictionaries
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "cases",
                where_conditions={"responsibility_id": responsibility_id},
                order_by="date_reported DESC",
            )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(
                f"Failed to get cases by responsibility {responsibility_id}: {e}"
            )
            return []

    def update_case(self, case_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a case with the provided data.

        Args:
            case_id: The case ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add updated_date if not provided
            if "updated_date" not in updates:
                updates["updated_date"] = datetime.now().isoformat()

            query, params = SQLBuilder.build_update_query(
                "cases", updates, "id = ?", [case_id]
            )
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to update case {case_id}: {e}")
            return False

    def create_case(self, case_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new case.

        Args:
            case_data: Case data dictionary

        Returns:
            New case ID if successful, None otherwise
        """
        try:
            # Add created_date if not provided
            if "date_reported" not in case_data:
                case_data["date_reported"] = datetime.now().date().isoformat()

            query, params = SQLBuilder.build_insert_query("cases", case_data)
            self.db_manager.execute_update(query, params)

            # Get the last inserted row ID
            result = self.db_manager.execute_query("SELECT last_insert_rowid() as id")
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Failed to create case: {e}")
            return None

    def delete_case(self, case_id: int) -> bool:
        """
        Delete a case by ID.

        Args:
            case_id: The case ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM cases WHERE id = ?", [case_id]
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to delete case {case_id}: {e}")
            return False

    def search_cases(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        responsibility_id: Optional[int] = None,
        fy_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search cases with multiple filters.

        Args:
            search_term: Text to search in transaction_no, description, reference_no
            status: Case status filter
            responsibility_id: Responsibility ID filter
            fy_id: Financial year ID filter
            limit: Maximum results to return

        Returns:
            List of matching case dictionaries
        """
        try:
            conditions = []
            params = []

            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    """
                    (transaction_no LIKE ? OR description LIKE ? OR reference_no LIKE ?)
                """
                )
                params.extend([search_pattern] * 3)

            if status:
                conditions.append("status = ?")
                params.append(status)

            if responsibility_id:
                conditions.append("responsibility_id = ?")
                params.append(responsibility_id)

            if fy_id:
                conditions.append("fy_id = ?")
                params.append(fy_id)

            where_clause = " AND ".join(conditions) if conditions else ""
            query = f"""
                SELECT * FROM cases
                {f"WHERE {where_clause}" if where_clause else ""}
                ORDER BY date_reported DESC
                LIMIT ?
            """
            params.append(limit)

            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to search cases: {e}")
            return []

    def get_case_count_by_status(self) -> Dict[str, int]:
        """
        Get count of cases grouped by status.

        Returns:
            Dictionary mapping status to count
        """
        try:
            query = """
                SELECT status, COUNT(*) as count
                FROM cases
                GROUP BY status
                ORDER BY count DESC
            """
            results = self.db_manager.execute_query(query)
            return {row["status"]: row["count"] for row in results}
        except Exception as e:
            logger.error(f"Failed to get case counts by status: {e}")
            return {}

    def count_cases_by_status(self, status: str) -> int:
        """
        Get count of cases with a specific status.

        Args:
            status: Case status to count

        Returns:
            Number of cases with the specified status
        """
        try:
            query = "SELECT COUNT(*) as count FROM cases WHERE status = ?"
            results = self.db_manager.execute_query(query, [status])
            return results[0]["count"] if results else 0
        except Exception as e:
            logger.error(f"Failed to count cases by status '{status}': {e}")
            return 0

    def bulk_update_status(self, case_ids: List[int], new_status: str) -> int:
        """
        Bulk update status for multiple cases.

        Args:
            case_ids: List of case IDs to update
            new_status: New status to set

        Returns:
            Number of cases updated
        """
        try:
            if not case_ids:
                return 0

            placeholders = ", ".join("?" * len(case_ids))
            query = f"""
                UPDATE cases
                SET status = ?, updated_date = ?
                WHERE id IN ({placeholders})
            """
            params = [new_status, datetime.now().isoformat()] + case_ids

            return self.db_manager.execute_update(query, params)
        except Exception as e:
            logger.error(f"Failed to bulk update case status: {e}")
            return 0

    def count_cases(self) -> int:
        """
        Get total count of all cases.

        Returns:
            Total number of cases
        """
        try:
            query = "SELECT COUNT(*) as count FROM cases"
            results = self.db_manager.execute_query(query)
            return results[0]["count"] if results else 0
        except Exception as e:
            logger.error(f"Failed to count cases: {e}")
            return 0

    def get_recent_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent cases.

        Args:
            limit: Maximum number of cases to return

        Returns:
            List of recent case dictionaries
        """
        try:
            query, params = SQLBuilder.build_select_query(
                "cases",
                order_by="date_reported DESC",
                limit=limit,
            )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get recent cases: {e}")
            return []

    def get_cases_with_filters(
        self,
        status: Optional[str] = None,
        financial_year: Optional[str] = None,
        fy_id: Optional[int] = None,
        assessment_status: Optional[str] = None,
        responsibility_id: Optional[int] = None,
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get cases with optional filters.

        Args:
            status: Filter by case status
            financial_year: Filter by financial year string (legacy)
            fy_id: Filter by financial year ID
            assessment_status: Filter by assessment status
            responsibility_id: Filter by responsibility ID
            search_term: Search in transaction_no, category, or description
            limit: Maximum number of results

        Returns:
            List of case dictionaries
        """
        try:
            conditions = {}
            params = []

            if status and status != "All":
                conditions["status"] = status

            if financial_year and financial_year != "All":
                conditions["financial_year"] = financial_year

            if fy_id is not None:
                conditions["fy_id"] = fy_id

            if assessment_status and assessment_status != "All Assessment Statuses":
                conditions["assessment_status"] = assessment_status

            if responsibility_id is not None:
                conditions["responsibility_id"] = responsibility_id

            # Handle search term with LIKE queries
            search_conditions = {}
            if search_term:
                search_conditions = {
                    "transaction_no": f"%{search_term}%",
                    "category": f"%{search_term}%",
                    "description": f"%{search_term}%"
                }

            # Handle search term separately since SQLBuilder doesn't support LIKE queries
            if search_term:
                # Build query manually when search is involved
                query = "SELECT * FROM cases"
                where_clauses = []
                search_params = []

                # Add regular conditions
                for column, value in conditions.items():
                    where_clauses.append(f"{column} = ?")
                    params.append(value)

                # Add search conditions
                search_fields = ["transaction_no", "category", "description"]
                search_clauses = []
                for field in search_fields:
                    search_clauses.append(f"{field} LIKE ?")
                    search_params.append(f"%{search_term}%")

                if search_clauses:
                    search_condition = " OR ".join(search_clauses)
                    if where_clauses:
                        where_clauses.append(f"({search_condition})")
                    else:
                        where_clauses.append(search_condition)
                    params.extend(search_params)

                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                query += " ORDER BY date_reported DESC"

                if limit:
                    query += f" LIMIT {limit}"
            else:
                query, params = SQLBuilder.build_select_query(
                    "cases",
                    where_conditions=conditions,
                    order_by="date_reported DESC",
                    limit=limit,
                )
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get cases with filters: {e}")
            return []
