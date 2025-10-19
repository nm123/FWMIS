"""
Coordinator for case saving utilities.
"""

from .case_save_db_utils import update_database_and_workflow
from .case_save_file_utils import handle_file_operations
from .case_save_validation_utils import validate_case_data


def save_case(dialog_instance) -> bool:
    """Orchestrate case saving: validate, handle files, update DB/workflow."""
    try:
        # Call validate_case_data
        if not validate_case_data(dialog_instance):
            return False

        # Prepare case dict (existing code)
        # Convert dates to strings, handling NULL dates
        date_incurred_str = dialog_instance.date_incurred_edit.date().toString(
            "yyyy-MM-dd"
        )
        date_identified_str = dialog_instance.date_identified_edit.date().toString(
            "yyyy-MM-dd"
        )
        date_reported_str = dialog_instance.date_reported_edit.date().toString(
            "yyyy-MM-dd"
        )

        # Handle BAS dates - use NULL if text field is empty
        bas_payment_date_text = dialog_instance.bas_payment_date_edit.text().strip()
        bas_payment_date_str = bas_payment_date_text if bas_payment_date_text else None

        bas_journal_date_text = dialog_instance.bas_journal_date_edit.text().strip()
        bas_journal_date_str = bas_journal_date_text if bas_journal_date_text else None

        # Create case dictionary
        category_text = dialog_instance.category_combo.currentText()
        status_text = dialog_instance.lc_status_combo.currentText()
        criminal_charges_text = dialog_instance.criminal_charges_combo.currentText()
        disciplinary_text = dialog_instance.disciplinary_combo.currentText()
        # loss_recovery_text is now handled by the recovery progress system

        # Get existing fy_id and period_id from case data, or set defaults if missing
        existing_fy_id = (
            dialog_instance.case_data[26]
            if len(dialog_instance.case_data) > 26
            else None
        )  # fy_id
        existing_period_id = (
            dialog_instance.case_data[27]
            if len(dialog_instance.case_data) > 27
            else None
        )  # period_id

        # If fy_id is missing, get current open financial year
        if existing_fy_id is None:
            from scripts.Utilities.financial_utils import (
                get_current_open_financial_year,
            )

            current_fy = get_current_open_financial_year()
            if current_fy:
                existing_fy_id = current_fy[0]
                print(
                    "DEBUG: Fixed NULL fy_id for case %s -> %s"
                    % (dialog_instance.base_transaction_no, existing_fy_id)
                )
            else:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.critical(
                    dialog_instance,
                    "Financial Year Error",
                    "Cannot save case: No open financial year found.\n\n"
                    "Please ensure a financial year is open in Financial Year Management.",
                )
                return False

        # If period_id is missing, try to determine it from the date incurred
        if existing_period_id is None and existing_fy_id:
            try:
                import sqlite3

                from scripts.Utilities.config import DB_PATH

                conn_temp = sqlite3.connect(DB_PATH)
                cursor_temp = conn_temp.cursor()

                # Find the period that contains the date incurred
                cursor_temp.execute(
                    """
                    SELECT p.id FROM periods p
                    INNER JOIN financial_years fy ON p.fy_id = fy.id
                    WHERE p.fy_id = ? AND p.start_date <= ? AND p.end_date >= ?
                    ORDER BY p.period_number DESC LIMIT 1
                """,
                    (existing_fy_id, date_incurred_str, date_incurred_str),
                )
                period_result = cursor_temp.fetchone()
                existing_period_id = period_result[0] if period_result else None

                conn_temp.close()
            except Exception as e:
                print(f"Warning: Could not determine period ID: {e}")
                existing_period_id = None

        # Handle transaction_no suffix changes
        import re

        base_transaction_no = re.sub(
            r"(-LS|-WOR|-REC|-WO)+$", "", dialog_instance.base_transaction_no
        )
        has_ls = (
            "-LS" in dialog_instance.case_data[32]
            if len(dialog_instance.case_data) > 32
            else False
        )

        if dialog_instance.selected_list == "Lead Schedule":
            assessment_status_text = "Confirmed"
            lc_status_text = status_text
            if lc_status_text == "Write Off Recommended":
                if has_ls:
                    transaction_no_with_suffix = f"{base_transaction_no}-LS-WOR"
                else:
                    transaction_no_with_suffix = f"{base_transaction_no}-WOR"
            else:
                transaction_no_with_suffix = f"{base_transaction_no}-LS"
            list_text = "Lead Schedule"
        else:
            assessment_status_text = status_text
            lc_status_text = None
            if assessment_status_text == "Confirmed":
                transaction_no_with_suffix = f"{base_transaction_no}-LS"
                list_text = "Lead Schedule"
            elif assessment_status_text == "Write Off Recommended":
                transaction_no_with_suffix = f"{base_transaction_no}-WOR"
                list_text = "Write-Off Recommended"
            else:
                transaction_no_with_suffix = base_transaction_no
                list_text = "Checklist"

        # Compute suffixes from transaction_no_with_suffix
        suffixes_list = []
        if "-LS" in transaction_no_with_suffix:
            suffixes_list.append("-LS")
        if "-WOR" in transaction_no_with_suffix:
            suffixes_list.append("-WOR")
        if "-REC" in transaction_no_with_suffix:
            suffixes_list.append("-REC")
        if "-WO" in transaction_no_with_suffix:
            suffixes_list.append("-WO")

        suffixes = ",".join(suffixes_list)

        if lc_status_text == "Write Off Recommended":
            suffixes = ",".join([s for s in suffixes.split(",") if s != "-WO"])

        print(f"has_ls: {has_ls}, suffixes: {suffixes}")

        case = {
            "base_transaction_no": dialog_instance.base_transaction_no,
            "transaction_no": transaction_no_with_suffix,
            "suffixes": suffixes,
            "list": list_text,
            "date_incurred": str(date_incurred_str),
            "date_identified": str(date_identified_str),
            "date_reported": str(date_reported_str),
            "description": dialog_instance.description_edit.toPlainText().strip(),
            "bas_payment_no": dialog_instance.bas_payment_no_edit.text().strip(),
            "bas_payment_date": bas_payment_date_str,
            "bas_journal_no": dialog_instance.bas_journal_no_edit.text().strip(),
            "bas_journal_date": bas_journal_date_str,
            "persal_no": dialog_instance.persal_no_edit.text().strip(),
            "category": category_text,
            "responsibility_id": dialog_instance.selected_responsibility_id,
            "amount": float(dialog_instance.amount_edit.text().strip()),
            "source_document": dialog_instance.source_doc_edit.text().strip(),
            "supporting_evidence_path": dialog_instance.supporting_evidence_edit.text().strip(),
            "minutes": dialog_instance.minutes_edit.text().strip(),
            "evidence_path": dialog_instance.assessment_evidence_edit.text().strip(),
            "recovery_evidence_path": dialog_instance.recovery_evidence_edit.text().strip(),
            "criminal_charges": criminal_charges_text,
            "disciplinary_process": disciplinary_text,
            "loss_recovery": "N/A",  # Now handled by recovery progress system
            "assessment_status": assessment_status_text,
            "lc_status": lc_status_text,
            "prevention_steps": dialog_instance.prevention_steps_edit.toPlainText().strip(),
            "fy_id": existing_fy_id,
            "period_id": existing_period_id,
        }
        print(f"DEBUG: case lc_status = {case.get('lc_status')}")

        # Call handle_file_operations
        case = handle_file_operations(dialog_instance, case)

        # Call update_database_and_workflow
        result = update_database_and_workflow(dialog_instance, case)
        if result:
            dialog_instance.accept()
        return result

    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(dialog_instance, "Error", f"Failed to save case: {str(e)}")
        return False
