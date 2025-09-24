"""
Validation utilities for case saving.
"""

import json
import os
import sqlite3

from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.config import DB_PATH


def validate_case_data(dialog_instance) -> bool:
    """Validate BAS, amount, and evidence requirements."""
    # Check if case is finalized
    if (
        len(dialog_instance.case_data) > 26 and dialog_instance.case_data[26]
    ):  # is_finalized
        QMessageBox.warning(
            dialog_instance,
            "Case Finalized",
            "This case has been finalized and cannot be modified.\n\n"
            "Finalized cases are read-only for audit purposes.",
        )
        return False

    bas_payment_no = dialog_instance.bas_payment_no_edit.text().strip()
    bas_journal_no = dialog_instance.bas_journal_no_edit.text().strip()
    persal_no = dialog_instance.persal_no_edit.text().strip()
    amount_text = dialog_instance.amount_edit.text().strip()

    # Get compulsory settings from selected category
    category_name = dialog_instance.category_combo.currentText()
    category = next(
        (c for c in dialog_instance.categories if c["name"] == category_name), None
    )
    if category:
        bas_comp = category.get("bas_payment_compulsory", False)
        persal_comp = category.get("persal_compulsory", False)
    else:
        bas_comp = False
        persal_comp = False

    # Check compulsory fields based on category settings
    # Only validate BAS/Persal when those fields are visible (i.e., when category requires them)
    missing_fields = []
    # BAS requirement satisfied by either Payment No OR Journal No
    if bas_comp and not (bas_payment_no or bas_journal_no):
        missing_fields.append("BAS Payment No or BAS Journal No")
    if persal_comp and not persal_no:
        missing_fields.append("Persal No")
    if not amount_text:
        missing_fields.append("Amount")

    # Only show validation errors for BAS/Persal if the fields are actually visible
    # This prevents blocking saves when user is only uploading assessment evidence
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
            dialog_instance,
            "Invalid Input",
            f"The following fields are required: {', '.join(missing_fields)}",
        )
        return False

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        QMessageBox.warning(
            dialog_instance, "Invalid Input", "Amount must be a positive number."
        )
        return False

    # Use selected responsibility or existing one from case data
    if not dialog_instance.selected_responsibility_id:
        # Try to get responsibility_id from original case data
        if isinstance(dialog_instance.case_data, dict):
            dialog_instance.selected_responsibility_id = dialog_instance.case_data.get(
                "responsibility_id"
            )
        elif len(dialog_instance.case_data) > 11:
            dialog_instance.selected_responsibility_id = dialog_instance.case_data[11]

    if not dialog_instance.selected_responsibility_id:
        QMessageBox.warning(
            dialog_instance, "Invalid Input", "Please select a responsibility."
        )
        return False

    # Validate Loss Control fields
    loss_control_status = dialog_instance.lc_status_combo.currentText()
    if (
        loss_control_status == "Recovered"
        and not dialog_instance.recovery_evidence_edit.text().strip()
    ):
        QMessageBox.warning(
            dialog_instance,
            "Recovery Evidence Required",
            "Recovery evidence is required when status is 'Recovered'.\n\n"
            "Please select a recovery evidence file before saving.",
        )
        return False

    # Validate LC Minutes for Recovered or Write Off Recommended
    if (
        loss_control_status in ["Recovered", "Write Off Recommended"]
        and not dialog_instance.minutes_edit.text().strip()
    ):
        QMessageBox.warning(
            dialog_instance,
            "Loss Control Minutes Required",
            f"Loss Control Minutes are required when status is '{loss_control_status}'.\n\n"
            "Please select a Loss Control Minutes file before saving.",
        )
        return False

    # Validate Assessment Evidence for Valid/Confirmed statuses
    selected_assessment_status = dialog_instance.assessment_status_combo.currentText()
    if selected_assessment_status in ["Valid", "Confirmed"]:
        # Check if evidence exists in the current evidence field (uploaded during this session)
        current_evidence_path = dialog_instance.assessment_evidence_edit.text().strip()
        
        # Also check if evidence already exists in the database
        existing_evidence = False
        if hasattr(dialog_instance, 'case_id') and dialog_instance.case_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT evidence_paths FROM cases WHERE id = ?", (dialog_instance.case_id,))
            evidence_data = cursor.fetchone()
            conn.close()
            
            if evidence_data and evidence_data[0]:
                try:
                    evidence_dict = json.loads(evidence_data[0])
                    if evidence_dict and (evidence_dict.get("assessment_evidence") or evidence_dict.get("assessment")):
                        existing_evidence = True
                except json.JSONDecodeError:
                    pass
        else:
            # Fallback: check by transaction_no if case_id not available
            if hasattr(dialog_instance, 'base_transaction_no') and dialog_instance.base_transaction_no:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT evidence_paths FROM cases WHERE base_transaction_no = ?", (dialog_instance.base_transaction_no,))
                evidence_data = cursor.fetchone()
                conn.close()
                
                if evidence_data and evidence_data[0]:
                    try:
                        evidence_dict = json.loads(evidence_data[0])
                        if evidence_dict and (evidence_dict.get("assessment_evidence") or evidence_dict.get("assessment")):
                            existing_evidence = True
                    except json.JSONDecodeError:
                        pass

        # Require evidence if not in current session AND not in database
        if (not current_evidence_path or not os.path.exists(current_evidence_path)) and not existing_evidence:
            QMessageBox.warning(
                dialog_instance,
                "Cannot Save",
                f"Cannot save: Assessment evidence required for {selected_assessment_status} status.\n\n"
                "Please upload assessment evidence before saving.",
            )
            print(
                f"LOG: Blocked save for case {dialog_instance.base_transaction_no} due to missing assessment evidence"
            )
            return False

        print(
            f"LOG: Found assessment evidence for case {dialog_instance.base_transaction_no}: {current_evidence_path or 'existing in database'}"
        )

    # Validate LC evidence for LC statuses
    selected_lc_status = dialog_instance.lc_status_combo.currentText()
    if selected_lc_status in ["Recovered", "Write-Off Recommended"]:
        if (
            selected_lc_status == "Recovered"
            and not dialog_instance.recovery_evidence_edit.text().strip()
        ):
            QMessageBox.warning(
                dialog_instance,
                "Recovery Evidence Required",
                "Recovery evidence is required when Loss Control status is 'Recovered'.",
            )
            return False
        if not dialog_instance.minutes_edit.text().strip():
            QMessageBox.warning(
                dialog_instance,
                "Loss Control Minutes Required",
                f"Loss Control Minutes are required when status is '{selected_lc_status}'.",
            )
            return False

    return True
