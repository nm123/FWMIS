"""
Recovery and installment management handlers for the Edit Case dialog.

This module contains all functions related to recovery tracking, installment
management, and recovery progress updates.
"""

from typing import Any

from PyQt5.QtWidgets import QMessageBox


def add_new_installment(dialog: Any) -> None:
    """
    Add a new installment to the recovery tracking.

    Args:
        dialog: The EditCaseDialog instance
    """
    try:
        # Validate installment amount
        amount_text = dialog.new_installment_amount_edit.text().strip()
        if not amount_text:
            QMessageBox.warning(
                dialog, "Validation Error", "Please enter an installment amount."
            )
            return

        try:
            installment_amount = float(amount_text)
            if installment_amount <= 0:
                QMessageBox.warning(
                    dialog,
                    "Validation Error",
                    "Installment amount must be greater than zero.",
                )
                return
        except ValueError:
            QMessageBox.warning(
                dialog, "Validation Error", "Please enter a valid amount."
            )
            return

        # Validate installment date
        date_text = dialog.new_installment_date_edit.text().strip()
        if not date_text:
            QMessageBox.warning(
                dialog, "Validation Error", "Please select an installment date."
            )
            return

        # Validate that recovery evidence is uploaded (latest Debt Inquiry report required)
        recovery_evidence_text = (
            dialog.recovery_evidence_rip_edit.text().strip()
            if hasattr(dialog, "recovery_evidence_rip_edit")
            and dialog.recovery_evidence_rip_edit.isVisible()
            else dialog.recovery_evidence_edit.text().strip()
        )

        if not recovery_evidence_text:
            QMessageBox.warning(
                dialog,
                "Recovery Evidence Required",
                "Latest Debt Inquiry report must be uploaded before adding an installment.\n\n"
                "This ensures all recovery activities are properly documented with current evidence.\n\n"
                "Please upload the latest Debt Inquiry report and try again.",
            )
            return

        # Get current recovery data
        current_amount_paid = get_current_amount_paid(dialog)
        original_amount = get_original_amount(dialog)

        # Check if installment would exceed original amount
        new_total = current_amount_paid + installment_amount
        if new_total > original_amount:
            QMessageBox.warning(
                dialog,
                "Validation Error",
                f"Installment would exceed original amount.\n"
                f"Original: R {original_amount:.2f}\n"
                f"Already paid: R {current_amount_paid:.2f}\n"
                f"Remaining: R {original_amount - current_amount_paid:.2f}",
            )
            return

        # Save installment to database
        if save_installment_to_database(dialog, installment_amount, date_text):
            # Update recovery progress
            update_recovery_progress(dialog)

            # Clear form
            dialog.new_installment_amount_edit.clear()
            dialog.new_installment_date_edit.clear()

            # Check if fully recovered
            if new_total >= original_amount:
                finalize_recovery(dialog)

            QMessageBox.information(
                dialog,
                "Success",
                f"Installment of R {installment_amount:.2f} added successfully with evidence documentation!",
            )
        else:
            QMessageBox.critical(
                dialog, "Error", "Failed to save installment. Please try again."
            )

    except Exception as e:
        QMessageBox.critical(dialog, "Error", f"An error occurred: {str(e)}")


def view_installment_history(dialog: Any) -> None:
    """
    Open installment history dialog with summary information.

    Args:
        dialog: The EditCaseDialog instance
    """
    try:
        # For now, show a simple message box with installment summary
        current_amount_paid = get_current_amount_paid(dialog)
        original_amount = get_original_amount(dialog)
        remaining_amount = original_amount - current_amount_paid

        QMessageBox.information(
            dialog,
            "Installment History",
            f"Recovery Progress Summary:\n\n"
            f"Original Amount: R {original_amount:.2f}\n"
            f"Amount Paid: R {current_amount_paid:.2f}\n"
            f"Remaining: R {remaining_amount:.2f}\n\n"
            f"Progress: {(current_amount_paid/original_amount*100):.1f}%",
        )
    except Exception as e:
        QMessageBox.critical(
            dialog, "Error", f"Failed to open installment history: {str(e)}"
        )


def update_recovery_progress(dialog: Any) -> None:
    """
    Update recovery progress display with current amounts.

    Args:
        dialog: The EditCaseDialog instance
    """
    try:
        original_amount = get_original_amount(dialog)
        amount_paid = get_current_amount_paid(dialog)
        remaining_amount = original_amount - amount_paid

        # Update labels
        dialog.original_amount_label.setText(f"R {original_amount:.2f}")
        dialog.amount_paid_label.setText(f"R {amount_paid:.2f}")
        dialog.remaining_amount_label.setText(f"R {remaining_amount:.2f}")

        # Update recovery status
        if amount_paid == 0:
            dialog.loss_recovery_status_label.setText("N/A")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #666; padding: 5px; border: 1px solid #ddd; background-color: #f9f9f9; }"
            )
        elif remaining_amount > 0:
            dialog.loss_recovery_status_label.setText("In Progress")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #ff9800; padding: 5px; border: 1px solid #ddd; background-color: #fff3e0; }"
            )
        else:
            dialog.loss_recovery_status_label.setText("Completed")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #4caf50; padding: 5px; border: 1px solid #ddd; background-color: #f1f8e9; }"
            )

    except Exception as e:
        print(f"Error updating recovery progress: {e}")


def get_original_amount(dialog: Any) -> float:
    """
    Get the original case amount from the amount field.

    Args:
        dialog: The EditCaseDialog instance

    Returns:
        float: The original amount, or 0.0 if not available
    """
    try:
        amount_text = dialog.amount_edit.text().strip()
        if amount_text:
            return float(amount_text)
        return 0.0
    except (ValueError, AttributeError):
        return 0.0


def get_current_amount_paid(dialog: Any) -> float:
    """
    Get current total amount paid from database installments.

    Args:
        dialog: The EditCaseDialog instance

    Returns:
        float: The total amount paid, or 0.0 if error
    """
    try:
        import sqlite3

        from scripts.Utilities.config import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get total from installments table
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM installments WHERE case_id = ?",
            (dialog.case_id,),
        )
        result = cursor.fetchone()
        conn.close()

        return float(result[0]) if result else 0.0
    except Exception as e:
        print(f"Error getting current amount paid: {e}")
        return 0.0


def save_installment_to_database(dialog: Any, amount: float, date: str) -> bool:
    """
    Save installment to database.

    Args:
        dialog: The EditCaseDialog instance
        amount: The installment amount
        date: The installment date

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import sqlite3
        from datetime import datetime

        from scripts.Utilities.config import DB_PATH

        conn = sqlite3.connect(DB_PATH)
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
            (dialog.case_id, amount, date, datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Error saving installment: {e}")
        return False


def finalize_recovery(dialog: Any) -> None:
    """
    Finalize recovery when fully paid and update case status.

    Args:
        dialog: The EditCaseDialog instance
    """
    try:
        # Check if recovery evidence is uploaded before finalizing
        recovery_evidence_path = (
            dialog.recovery_evidence_rip_edit.text().strip()
            if hasattr(dialog, "recovery_evidence_rip_edit")
            and dialog.recovery_evidence_rip_edit.text().strip()
            else dialog.recovery_evidence_edit.text().strip()
        )

        if not recovery_evidence_path:
            QMessageBox.warning(
                dialog,
                "Recovery Evidence Required",
                "Recovery has been completed, but recovery evidence must be uploaded before finalizing the case.\n\n"
                "Please upload recovery evidence and save the case to complete the finalization.",
            )
            # Don't finalize yet - let user upload evidence and save manually
            return

        # Update case status to Recovered
        dialog.lc_status_combo.setCurrentText("Recovered")

        # Update list status
        from .ui_updaters import update_list_status_grid

        dialog.update_list_status_grid("Recovered", "Recovered")
        dialog.update_list_status_grid("Recovery in Progress", "N/A")

        # Update workflow - this will add -REC suffix and remove -RIP suffix
        # Skip evidence check since we already validated it above
        from scripts.Utilities.workflow_utils import handle_loss_control_status_change

        success = handle_loss_control_status_change(
            dialog.case_id,
            dialog.base_transaction_no,
            "Recovered",
            skip_evidence_check=True,
        )

        if success:
            # Update the dialog's suffixes to reflect the change
            # dialog.suffixes is already a list, so we work with it directly
            if isinstance(dialog.suffixes, list):
                dialog.suffixes = [s for s in dialog.suffixes if s != "-RIP"]
                if "-REC" not in dialog.suffixes:
                    dialog.suffixes.append("-REC")
            else:
                # If it's a string, convert to list first
                suffix_list = dialog.suffixes.split(",") if dialog.suffixes else []
                suffix_list = [s for s in suffix_list if s != "-RIP"]
                if "-REC" not in suffix_list:
                    suffix_list.append("-REC")
                dialog.suffixes = suffix_list

            # Update the transaction number display
            from scripts.Utilities.workflow_utils import get_display_transaction_no

            display_transaction_no = get_display_transaction_no(
                dialog.base_transaction_no, dialog.suffixes
            )
            dialog.trans_no_edit.setText(display_transaction_no)

            QMessageBox.information(
                dialog,
                "Recovery Completed",
                "This case has been fully recovered and moved to the Recovered list!",
            )
        else:
            QMessageBox.warning(
                dialog,
                "Warning",
                "Recovery completed but workflow update failed. Please refresh the case.",
            )

    except Exception as e:
        print(f"Error finalizing recovery: {e}")
        QMessageBox.warning(
            dialog, "Warning", f"Recovery completed but status update failed: {str(e)}"
        )


def on_save_clicked(dialog: Any) -> None:
    """Handle save button click."""
    dialog.logic.save_case()


def on_cancel_clicked(dialog: Any) -> None:
    """Handle cancel button click."""
    dialog.reject()
