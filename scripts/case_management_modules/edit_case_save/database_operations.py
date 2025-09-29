"""
Database Operations Module for Edit Case Save

Contains database operations for saving case data.
"""

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class DatabaseOperations:
    """
    Handles database operations for saving case data.
    """

    @staticmethod
    def save_case_to_database(dialog: "QWidget", case_data: Dict) -> bool:
        """
        Save case data to the database.

        Args:
            dialog: The EditCaseDialog instance
            case_data: Prepared case data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from datetime import datetime

            from scripts.Utilities.db_utils import get_db_connection

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Prepare update data
                update_data = {
                    "transaction_no": case_data["transaction_no"],
                    "description": case_data["description"],
                    "reference_no": case_data["reference_no"],
                    "category_id": case_data["category_id"],
                    "responsibility_id": case_data["responsibility_id"],
                    "amount": case_data["amount"],
                    "bas_payment_no": case_data["bas_payment_no"],
                    "bas_journal_no": case_data["bas_journal_no"],
                    "bas_payment_date": case_data["bas_payment_date"],
                    "bas_journal_date": case_data["bas_journal_date"],
                    "persal_no": case_data["persal_no"],
                    "source_document_path": case_data.get("source_document_path"),
                    "minutes_path": case_data.get("minutes_path"),
                    "assessment_evidence_path": case_data.get(
                        "assessment_evidence_path"
                    ),
                    "supporting_evidence_path": case_data.get(
                        "supporting_evidence_path"
                    ),
                    "recovery_evidence_path": case_data.get("recovery_evidence_path"),
                    "recovery_evidence_rip_path": case_data.get(
                        "recovery_evidence_rip_path"
                    ),
                    "updated_date": datetime.now().isoformat(),
                }

                # Add status fields if they exist
                if "status" in case_data:
                    update_data["status"] = case_data["status"]
                if "assessment_status" in case_data:
                    update_data["assessment_status"] = case_data["assessment_status"]
                if "lc_status" in case_data:
                    update_data["lc_status"] = case_data["lc_status"]
                if "assessed_by" in case_data:
                    update_data["assessed_by"] = case_data["assessed_by"]
                if "assessment_date" in case_data:
                    update_data["assessment_date"] = case_data["assessment_date"]

                # Build safe update query
                from scripts.Utilities.sql_builder import safe_update

                query, params = safe_update("cases", update_data, "id", dialog.case_id)

                cursor.execute(query, params)

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "CASE_UPDATED",
                f"Case {case_data['transaction_no']} updated",
                dialog.case_id,
            )

            return True

        except Exception as e:
            from scripts.Utilities.message_box_utils import show_error_message

            show_error_message(
                dialog, "Database Error", f"Failed to save case: {str(e)}"
            )
            return False

    @staticmethod
    def save_installment_to_database(dialog: "QWidget", installment_data: Dict) -> bool:
        """
        Save installment data to the database.

        Args:
            dialog: The EditCaseDialog instance
            installment_data: Prepared installment data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from datetime import datetime

            from scripts.Utilities.db_utils import get_db_connection

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Create installments table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS installments (
                        id INTEGER PRIMARY KEY,
                        case_id INTEGER,
                        amount REAL,
                        installment_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY (case_id) REFERENCES cases (id)
                    )
                """
                )

                # Insert installment
                cursor.execute(
                    """
                    INSERT INTO installments (case_id, amount, installment_date, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        installment_data["case_id"],
                        installment_data["amount"],
                        installment_data["date"],
                        datetime.now().isoformat(),
                    ),
                )

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "INSTALLMENT_ADDED",
                f"Installment of R{installment_data['amount']:.2f} added to case {dialog.case_id}",
                dialog.case_id,
            )

            return True

        except Exception as e:
            print(f"Error saving installment: {e}")
            return False

    @staticmethod
    def update_case_statuses(dialog: "QWidget") -> None:
        """
        Update related case statuses after save operations.

        Args:
            dialog: The EditCaseDialog instance
        """
        try:
            # Update any related workflow statuses
            if hasattr(dialog, "base_transaction_no") and hasattr(dialog, "suffixes"):
                from scripts.Utilities.workflow_utils import update_workflow_status

                update_workflow_status(dialog.base_transaction_no, dialog.suffixes)

        except Exception as e:
            print(f"Error updating case statuses: {e}")

    @staticmethod
    def finalize_recovery_if_complete(dialog: "QWidget") -> None:
        """
        Check if recovery is complete and finalize if needed.

        Args:
            dialog: The EditCaseDialog instance
        """
        try:
            from scripts.case_management_modules.edit_case_save.recovery_handlers import (
                finalize_recovery,
            )

            finalize_recovery(dialog)
        except Exception as e:
            print(f"Error finalizing recovery: {e}")
