"""
Validation Module for Edit Case Save Operations

Contains validation logic for case data before saving.
"""

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class CaseDataValidator:
    """
    Validates case data before saving to database.
    """

    @staticmethod
    def validate_case_data(dialog: "QWidget") -> bool:
        """
        Validate case data for saving.

        Args:
            dialog: The EditCaseDialog instance

        Returns:
            bool: True if validation passes, False otherwise
        """
        from PyQt5.QtWidgets import QMessageBox

        # Check if case is finalized
        if len(dialog.case_data) > 37 and dialog.case_data[37]:  # is_finalized
            QMessageBox.warning(
                dialog,
                "Case Finalized",
                "This case has been finalized and cannot be modified.\n\n"
                "Finalized cases are read-only for audit purposes.",
            )
            return False

        # Get form data
        bas_payment_no = dialog.bas_payment_no_edit.text().strip()
        bas_journal_no = dialog.bas_journal_no_edit.text().strip()
        persal_no = dialog.persal_no_edit.text().strip()
        amount_text = dialog.amount_edit.text().strip()

        # Get category settings
        category_name = dialog.category_combo.currentText()
        category = next(
            (c for c in dialog.categories if c["name"] == category_name), None
        )

        bas_comp = False
        persal_comp = False
        if category:
            bas_comp = category.get("bas_payment_compulsory", False)
            persal_comp = category.get("persal_compulsory", False)

        # Validate required fields
        missing_fields = []

        # BAS requirement satisfied by either Payment No OR Journal No
        if bas_comp and not (bas_payment_no or bas_journal_no):
            missing_fields.append("BAS Payment No or BAS Journal No")

        if persal_comp and not persal_no:
            missing_fields.append("Persal No")

        if not amount_text:
            missing_fields.append("Amount")

        # Check for BAS/Persal validation when fields are visible
        bas_validation_errors = []
        if bas_comp and not (bas_payment_no or bas_journal_no):
            bas_validation_errors.append("BAS Payment No or BAS Journal No")
        if persal_comp and not persal_no:
            bas_validation_errors.append("Persal No")

        # If only BAS/Persal validation errors and fields are not visible, don't block the save
        if bas_validation_errors and not any([bas_comp, persal_comp]):
            # User is not editing supporting evidence fields, allow save
            pass
        elif missing_fields:
            QMessageBox.warning(
                dialog,
                "Invalid Input",
                f"The following fields are required: {', '.join(missing_fields)}",
            )
            return False

        # Validate amount
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                dialog, "Invalid Input", "Amount must be a positive number."
            )
            return False

        return True

    @staticmethod
    def validate_supporting_evidence(dialog: "QWidget") -> bool:
        """
        Validate supporting evidence requirements.

        Args:
            dialog: The EditCaseDialog instance

        Returns:
            bool: True if validation passes, False otherwise
        """
        from PyQt5.QtWidgets import QMessageBox

        # Check supporting evidence compulsory flag
        if (
            hasattr(dialog, "supporting_evidence_compulsory")
            and dialog.supporting_evidence_compulsory
        ):
            supporting_evidence = dialog.supporting_evidence_edit.text().strip()
            if not supporting_evidence:
                QMessageBox.warning(
                    dialog,
                    "Supporting Evidence Required",
                    "Supporting Evidence is required before this case can be saved.\n\n"
                    "Please upload the supporting evidence document.",
                )
                return False

        # Check assessment evidence for Valid/Confirmed cases
        selected_status = ""
        if hasattr(dialog, "assessment_status_combo"):
            selected_status = dialog.assessment_status_combo.currentText()
        elif hasattr(dialog, "status_combo"):
            selected_status = dialog.status_combo.currentText()

        if selected_status in ["Valid", "Confirmed"]:
            assessment_evidence = dialog.assessment_evidence_edit.text().strip()
            if not assessment_evidence:
                QMessageBox.warning(
                    dialog,
                    "Assessment Evidence Required",
                    "Assessment Evidence is required for Valid and Confirmed cases.\n\n"
                    "Please upload the assessment evidence document.",
                )
                return False

        return True


def safe_float_conversion(value) -> float:
    """
    Safely convert a value to float, returning 0.0 if conversion fails.

    Args:
        value: Value to convert

    Returns:
        float: Converted value or 0.0
    """
    if not value or value.strip() == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
