"""
Database Checks Module for Import Operations

Contains database integrity checking functionality.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .worker_base import ImportWorker


class DatabaseIntegrityChecker:
    """
    Checks database integrity before import operations.
    """

    @staticmethod
    def check_database_integrity(worker: "ImportWorker") -> None:
        """
        Perform comprehensive database integrity checks before import.

        Args:
            worker: The ImportWorker instance

        Raises:
            Exception: If database integrity checks fail
        """
        import sqlite3

        from scripts.Utilities.db_utils import get_db_connection

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # Check 1: Required tables exist
            required_tables = [
                "cases",
                "categories",
                "responsibilities",
                "contacts",
                "financial_years",
                "case_status_history",
            ]

            for table in required_tables:
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=?
                """,
                    (table,),
                )

                if not cursor.fetchone():
                    raise Exception(f"Required table '{table}' does not exist")

            # Check 2: Categories table has required data
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                raise Exception("Categories table is empty - import cannot proceed")

            # Check 3: Responsibilities table has posting level responsibilities
            cursor.execute(
                """
                SELECT COUNT(*) FROM responsibilities
                WHERE is_posting_level = 1
            """
            )
            if cursor.fetchone()[0] == 0:
                raise Exception(
                    "No posting level responsibilities found - import cannot proceed"
                )

            # Check 4: Financial years are properly configured
            cursor.execute(
                """
                SELECT COUNT(*) FROM financial_years
                WHERE status = 'open'
            """
            )
            if cursor.fetchone()[0] == 0:
                raise Exception("No open financial year found - import cannot proceed")

            # Check 5: Database foreign key constraints
            cursor.execute("PRAGMA foreign_keys")
            if cursor.fetchone()[0] != 1:
                raise Exception("Foreign key constraints are not enabled")

            # Check 6: Check for any orphaned records
            cursor.execute(
                """
                SELECT COUNT(*) FROM contacts c
                LEFT JOIN responsibilities r ON c.responsibility_id = r.id
                WHERE r.id IS NULL
            """
            )
            orphaned_contacts = cursor.fetchone()[0]
            if orphaned_contacts > 0:
                raise Exception(f"Found {orphaned_contacts} orphaned contact records")

            # Check 7: Check for duplicate case numbers that might conflict
            # Exclude NULL transaction_no values as they represent legacy/incomplete cases
            cursor.execute(
                """
                SELECT transaction_no, COUNT(*) as count
                FROM cases
                WHERE transaction_no IS NOT NULL
                GROUP BY transaction_no
                HAVING count > 1
            """
            )
            duplicates = cursor.fetchall()
            if duplicates:
                duplicate_numbers = [row[0] for row in duplicates]
                raise Exception(
                    f"Found duplicate transaction numbers: {duplicate_numbers[:5]}..."
                )

            # Check 8: Verify database is not corrupted
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result and result[0] != "ok":
                raise Exception("Database integrity check failed")

            worker.progress.emit(0, "Database integrity check passed")

        except sqlite3.Error as e:
            raise Exception(f"Database error during integrity check: {str(e)}")
        finally:
            if conn:
                conn.close()
