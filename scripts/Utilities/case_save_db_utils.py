"""
Database and workflow utilities for case saving.
"""

import json
import sqlite3
from datetime import datetime

from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.workflow_utils import (
    handle_case_status_change, handle_loss_control_status_change)


def update_database_and_workflow(dialog_instance, case: dict) -> bool:
    """Perform DB update, commit, and workflow handling."""
    # Save to database with explicit transaction control
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        print(
            f"LOG: Started transaction for case {dialog_instance.base_transaction_no} save"
        )

        # Build evidence paths JSON
        evidence_paths = {}
        if case["evidence_path"]:
            evidence_paths["assessment"] = case["evidence_path"]
        if case["recovery_evidence_path"]:
            evidence_paths["recovery"] = case["recovery_evidence_path"]
        if case["minutes"]:
            evidence_paths["lc_minutes"] = case["minutes"]
        if case["supporting_evidence_path"]:
            evidence_paths["supporting"] = case["supporting_evidence_path"]
        if case["source_document"]:
            evidence_paths["source"] = case["source_document"]

        evidence_paths_json = json.dumps(evidence_paths) if evidence_paths else None

        assessment_status_text = case.get("assessment_status")
        lc_status_text = case.get("lc_status")
        print(
            f"DEBUG: assessment_status_text={assessment_status_text}, lc_status_text={lc_status_text}"
        )

        cursor.execute(
            """
            UPDATE cases SET
                date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                bas_payment_no = ?, bas_payment_date = ?, bas_journal_no = ?, bas_journal_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                base_transaction_no = ?, evidence_paths = ?, evidence_path = ?, transaction_no = ?, suffixes = ?, assessment_status = ?, lc_status = ?, criminal_charges = ?, disciplinary_process = ?,
                loss_recovery = ?, prevention_steps = ?
            WHERE id = ?
        """,
            (
                case["date_incurred"],
                case["date_identified"],
                case["date_reported"],
                case["description"],
                case["bas_payment_no"],
                case["bas_payment_date"],
                case["bas_journal_no"],
                case["bas_journal_date"],
                case["persal_no"],
                case["category"],
                case["responsibility_id"],
                case["amount"],
                case["base_transaction_no"],
                evidence_paths_json,
                case["evidence_path"],
                case["transaction_no"],
                case["suffixes"],
                assessment_status_text,
                lc_status_text,
                case["criminal_charges"],
                case["disciplinary_process"],
                case["loss_recovery"],
                case["prevention_steps"],
                dialog_instance.case_id,
            ),
        )

        print(
            f"LOG: Saved case {dialog_instance.base_transaction_no} with assessment_status='{assessment_status_text}', evidence_paths updated"
        )

        conn.commit()
        print(
            f"LOG: Committed transaction for case {dialog_instance.base_transaction_no} save"
        )
        case_id = dialog_instance.case_data[0]
        conn.close()

        # Workflow transitions are now handled in the status change handlers
        # No additional workflow processing needed here

        try:
            save_audit_log(
                "edit_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "base_transaction_no": dialog_instance.base_transaction_no,
                    "details": case,
                },
                dialog_instance.fy,
            )
        except Exception as audit_error:
            print(f"Warning: Failed to save audit log: {audit_error}")

        # Handle workflow status change for Valid/Confirmed if evidence exists
        selected_assessment_status = (
            dialog_instance.assessment_status_combo.currentText()
        )
        if selected_assessment_status in ["Valid", "Confirmed"]:
            if not handle_case_status_change(
                dialog_instance.case_id,
                dialog_instance.base_transaction_no,
                selected_assessment_status,
            ):
                QMessageBox.warning(
                    dialog_instance,
                    "Warning",
                    f"Case saved but workflow status update failed for {selected_assessment_status}",
                )
            else:
                print(
                    f"LOG: Updated workflow status to {selected_assessment_status} for case {dialog_instance.base_transaction_no}"
                )

        # Add LC workflow handling (new)
        selected_lc_status = (
            dialog_instance.lc_status_combo.currentText()
            if dialog_instance.lc_status_combo.isVisible()
            else None
        )
        if selected_lc_status and selected_lc_status != "Awaiting LC determination":
            if not handle_loss_control_status_change(
                dialog_instance.case_id,
                dialog_instance.base_transaction_no,
                selected_lc_status,
            ):
                QMessageBox.warning(
                    dialog_instance,
                    "Warning",
                    f"Case saved but LC workflow status update failed for {selected_lc_status}",
                )
            else:
                print(
                    f"LOG: Updated LC workflow status to {selected_lc_status} for case {dialog_instance.base_transaction_no}"
                )

        QMessageBox.information(
            dialog_instance, "Success", "Case updated successfully."
        )

        # Signal parent that case was modified
        dialog_instance.case_modified.emit()

        return True

    except Exception as e:
        print(f"DEBUG: Error during database operations: {e}")
        QMessageBox.critical(
            dialog_instance,
            "Database Error",
            f"Failed to save case to database: {str(e)}",
        )
        return False
