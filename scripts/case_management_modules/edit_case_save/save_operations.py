"""
Save Operations Module for Edit Case

Main interface module that coordinates the saving of case data.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class CaseSaveCoordinator:
    """
    Coordinates the saving of case data through validation, preparation, and database operations.
    """

    @staticmethod
    def save_case_components(dialog: "QWidget") -> None:
        """
        Save the case data to the database with validations and file operations.

        Args:
            dialog: The EditCaseDialog instance
        """
        from PyQt5.QtWidgets import QMessageBox

        try:
            # Import required modules
            from .data_preparation import CaseDataPreparer
            from .database_operations import DatabaseOperations
            from .validation import CaseDataValidator

            # Step 1: Validate data
            if not CaseDataValidator.validate_case_data(dialog):
                return

            if not CaseDataValidator.validate_supporting_evidence(dialog):
                return

            # Step 2: Prepare data
            case_data = CaseDataPreparer.prepare_case_data(dialog)
            if not case_data:
                return

            # Step 3: Save to database
            if not DatabaseOperations.save_case_to_database(dialog, case_data):
                return

            # Step 4: Handle installments if present
            installment_data = CaseDataPreparer.prepare_installment_data(dialog)
            if installment_data:
                if DatabaseOperations.save_installment_to_database(
                    dialog, installment_data
                ):
                    # Update recovery progress
                    from scripts.case_management_modules.edit_case_save.recovery_handlers import (
                        update_recovery_progress,
                    )

                    update_recovery_progress(dialog)

                    # Check if recovery is complete
                    DatabaseOperations.finalize_recovery_if_complete(dialog)

            # Step 5: Update related statuses
            DatabaseOperations.update_case_statuses(dialog)

            # Step 6: Show success message and close
            QMessageBox.information(dialog, "Success", "Case saved successfully!")

            # Close dialog after a short delay to show the message
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(1000, dialog.accept)

        except Exception as e:
            QMessageBox.critical(
                dialog,
                "Save Error",
                f"An unexpected error occurred while saving: {str(e)}",
            )
