"""
Data Preparation Module for Edit Case Save Operations

Contains logic for preparing and processing case data before saving.
"""

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class CaseDataPreparer:
    """
    Prepares and processes case data for saving.
    """

    @staticmethod
    def prepare_case_data(dialog: "QWidget") -> Optional[Dict]:
        """
        Prepare case data from dialog for saving.

        Args:
            dialog: The EditCaseDialog instance

        Returns:
            Dict containing prepared case data, or None if preparation fails
        """
        try:
            # Get basic form data
            data = CaseDataPreparer._extract_form_data(dialog)

            # Process category and responsibility
            data.update(CaseDataPreparer._process_category_and_responsibility(dialog))

            # Process financial data
            data.update(CaseDataPreparer._process_financial_data(dialog))

            # Process status and assessment data
            data.update(CaseDataPreparer._process_status_data(dialog))

            # Process evidence files
            data.update(CaseDataPreparer._process_evidence_files(dialog))

            return data

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                dialog,
                "Data Preparation Error",
                f"Failed to prepare case data: {str(e)}",
            )
            return None

    @staticmethod
    def _extract_form_data(dialog: "QWidget") -> Dict:
        """Extract basic form data from dialog."""
        return {
            "transaction_no": dialog.trans_no_edit.text().strip(),
            "description": dialog.description_edit.toPlainText().strip(),
            "reference_no": dialog.reference_no_edit.text().strip(),
            "source_doc": dialog.source_doc_edit.text().strip(),
            "minutes": dialog.minutes_edit.text().strip(),
            "assessment_evidence": dialog.assessment_evidence_edit.text().strip(),
            "supporting_evidence": dialog.supporting_evidence_edit.text().strip(),
            "recovery_evidence": getattr(dialog, "recovery_evidence_edit", None)
            and dialog.recovery_evidence_edit.text().strip(),
            "recovery_evidence_rip": getattr(dialog, "recovery_evidence_rip_edit", None)
            and dialog.recovery_evidence_rip_edit.text().strip(),
        }

    @staticmethod
    def _process_category_and_responsibility(dialog: "QWidget") -> Dict:
        """Process category and responsibility data."""
        # Category
        category_name = dialog.category_combo.currentText()
        category_id = None
        if dialog.categories:
            category = next(
                (c for c in dialog.categories if c["name"] == category_name), None
            )
            if category:
                category_id = category.get("id")

        # Responsibility
        responsibility_id = getattr(dialog, "selected_responsibility_id", None)
        if not responsibility_id and dialog.case_data:
            # Try to get from original case data (index 35 is responsibility_id)
            if len(dialog.case_data) > 35:
                responsibility_id = dialog.case_data[35]

        return {
            "category_id": category_id,
            "responsibility_id": responsibility_id,
        }

    @staticmethod
    def _process_financial_data(dialog: "QWidget") -> Dict:
        """Process financial data."""
        from .validation import safe_float_conversion

        # Basic financial data
        data = {
            "amount": safe_float_conversion(dialog.amount_edit.text().strip()),
            "bas_payment_no": dialog.bas_payment_no_edit.text().strip(),
            "bas_journal_no": dialog.bas_journal_no_edit.text().strip(),
            "persal_no": dialog.persal_no_edit.text().strip(),
        }

        # BAS dates
        if (
            hasattr(dialog, "bas_payment_date_edit")
            and dialog.bas_payment_date_edit.text()
        ):
            try:
                from datetime import datetime

                bas_payment_date = datetime.strptime(
                    dialog.bas_payment_date_edit.text().strip(), "%Y-%m-%d"
                ).date()
                data["bas_payment_date"] = bas_payment_date.isoformat()
            except ValueError:
                data["bas_payment_date"] = None
        else:
            data["bas_payment_date"] = None

        if (
            hasattr(dialog, "bas_journal_date_edit")
            and dialog.bas_journal_date_edit.text()
        ):
            try:
                from datetime import datetime

                bas_journal_date = datetime.strptime(
                    dialog.bas_journal_date_edit.text().strip(), "%Y-%m-%d"
                ).date()
                data["bas_journal_date"] = bas_journal_date.isoformat()
            except ValueError:
                data["bas_journal_date"] = None
        else:
            data["bas_journal_date"] = None

        return data

    @staticmethod
    def _process_status_data(dialog: "QWidget") -> Dict:
        """Process status and assessment data."""
        data = {}

        # Status selection
        if hasattr(dialog, "assessment_status_combo"):
            data["assessment_status"] = dialog.assessment_status_combo.currentText()
        elif hasattr(dialog, "status_combo"):
            data["status"] = dialog.status_combo.currentText()

        # LC Status
        if hasattr(dialog, "lc_status_combo"):
            data["lc_status"] = dialog.lc_status_combo.currentText()

        # Assessment data
        if hasattr(dialog, "assessed_by_edit"):
            data["assessed_by"] = dialog.assessed_by_edit.text().strip()

        if (
            hasattr(dialog, "assessment_date_edit")
            and dialog.assessment_date_edit.text()
        ):
            try:
                from datetime import datetime

                assessment_date = datetime.strptime(
                    dialog.assessment_date_edit.text().strip(), "%Y-%m-%d"
                ).date()
                data["assessment_date"] = assessment_date.isoformat()
            except ValueError:
                data["assessment_date"] = None

        return data

    @staticmethod
    def _process_evidence_files(dialog: "QWidget") -> Dict:
        """Process evidence file paths."""
        data = {}

        # File paths
        if hasattr(dialog, "source_doc_edit"):
            data["source_document_path"] = dialog.source_doc_edit.text().strip()

        if hasattr(dialog, "minutes_edit"):
            data["minutes_path"] = dialog.minutes_edit.text().strip()

        if hasattr(dialog, "assessment_evidence_edit"):
            data["assessment_evidence_path"] = (
                dialog.assessment_evidence_edit.text().strip()
            )

        if hasattr(dialog, "supporting_evidence_edit"):
            data["supporting_evidence_path"] = (
                dialog.supporting_evidence_edit.text().strip()
            )

        if hasattr(dialog, "recovery_evidence_edit"):
            data["recovery_evidence_path"] = (
                dialog.recovery_evidence_edit.text().strip()
            )

        if hasattr(dialog, "recovery_evidence_rip_edit"):
            data["recovery_evidence_rip_path"] = (
                dialog.recovery_evidence_rip_edit.text().strip()
            )

        return data

    @staticmethod
    def prepare_installment_data(dialog: "QWidget") -> Optional[Dict]:
        """
        Prepare installment data for saving.

        Args:
            dialog: The EditCaseDialog instance

        Returns:
            Dict containing installment data, or None
        """
        try:
            if not hasattr(dialog, "new_installment_amount_edit"):
                return None

            amount_text = dialog.new_installment_amount_edit.text().strip()
            date_text = dialog.new_installment_date_edit.text().strip()

            if not amount_text or not date_text:
                return None

            from .validation import safe_float_conversion

            amount = safe_float_conversion(amount_text)

            if amount <= 0:
                return None

            return {
                "amount": amount,
                "date": date_text,
                "case_id": dialog.case_id,
            }

        except Exception as e:
            print(f"Error preparing installment data: {e}")
            return None
