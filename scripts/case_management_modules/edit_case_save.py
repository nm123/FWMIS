"""
Save case utilities for EditCaseDialog.
Handles saving case data, validations, and file operations.
"""

import json
import os
import sqlite3
from datetime import datetime

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH


def save_case_components(dialog_instance):
    """
    Save the case data to the database with validations and file operations.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    try:
        # Check if case is finalized
        if (
            len(dialog_instance.case_data) > 37 and dialog_instance.case_data[37]
        ):  # is_finalized
            QMessageBox.warning(
                dialog_instance,
                "Case Finalized",
                "This case has been finalized and cannot be modified.\n\n"
                "Finalized cases are read-only for audit purposes.",
            )
            return
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
            return
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                dialog_instance, "Invalid Input", "Amount must be a positive number."
            )
            return
        # Use selected responsibility or existing one from case data
        if not dialog_instance.selected_responsibility_id:
            # Try to get responsibility_id from original case data
            if isinstance(dialog_instance.case_data, dict):
                dialog_instance.selected_responsibility_id = (
                    dialog_instance.case_data.get("responsibility_id")
                )
            elif len(dialog_instance.case_data) > 10:
                dialog_instance.selected_responsibility_id = dialog_instance.case_data[
                    10
                ]
        if not dialog_instance.selected_responsibility_id:
            QMessageBox.warning(
                dialog_instance, "Invalid Input", "Please select a responsibility."
            )
            return
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
            return
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
            return
        # Validate Assessment Evidence for Valid/Confirmed statuses
        selected_assessment_status = (
            dialog_instance.assessment_status_combo.currentText()
        )
        if selected_assessment_status in ["Valid", "Confirmed"]:
            # Check if evidence exists in the current evidence field (uploaded during this session)
            current_evidence_path = (
                dialog_instance.assessment_evidence_edit.text().strip()
            )
            if not current_evidence_path or not os.path.exists(current_evidence_path):
                QMessageBox.warning(
                    dialog_instance,
                    "Cannot Save",
                    f"Cannot save: Assessment evidence required for {selected_assessment_status} status.\n\n"
                    "Please upload assessment evidence before saving.",
                )
                print(
                    f"LOG: Blocked save for case {dialog_instance.base_transaction_no} due to missing assessment evidence"
                )
                return
            print(
                f"LOG: Found assessment evidence for case {dialog_instance.base_transaction_no}: {current_evidence_path}"
            )
        # Validate LC evidence for LC statuses
        selected_lc_status = dialog_instance.lc_status_combo.currentText()
        if selected_lc_status in ["Recovered", "Write Off Recommended"]:
            if (
                selected_lc_status == "Recovered"
                and not dialog_instance.recovery_evidence_edit.text().strip()
            ):
                QMessageBox.warning(
                    dialog_instance,
                    "Recovery Evidence Required",
                    "Recovery evidence is required when Loss Control status is 'Recovered'.",
                )
                return
            if not dialog_instance.minutes_edit.text().strip():
                QMessageBox.warning(
                    dialog_instance,
                    "Loss Control Minutes Required",
                    f"Loss Control Minutes are required when status is '{selected_lc_status}'.",
                )
                return
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
        assessment_status_text = dialog_instance.assessment_status_combo.currentText()
        lc_status_text = (
            dialog_instance.lc_status_combo.currentText()
            if dialog_instance.lc_status_combo.isVisible()
            else None
        )
        criminal_charges_text = dialog_instance.criminal_charges_combo.currentText()
        disciplinary_text = dialog_instance.disciplinary_combo.currentText()
        loss_recovery_text = dialog_instance.loss_recovery_combo.currentText()
        # Get existing fy_id and period_id from case data, or set defaults if missing
        existing_fy_id = (
            dialog_instance.case_data[21]
            if len(dialog_instance.case_data) > 21
            else None
        )  # fy_id
        existing_period_id = (
            dialog_instance.case_data[22]
            if len(dialog_instance.case_data) > 22
            else None
        )  # period_id
        # If fy_id is missing, get current open financial year
        if existing_fy_id is None:
            from scripts.Utilities.financial_utils import \
                get_current_open_financial_year

            current_fy = get_current_open_financial_year()
            if current_fy:
                existing_fy_id = current_fy[0]
                print(
                    f"DEBUG: Fixed NULL fy_id for case {dialog_instance.base_transaction_no}, set to {existing_fy_id}"
                )
            else:
                QMessageBox.critical(
                    dialog_instance,
                    "Financial Year Error",
                    "Cannot save case: No open financial year found.\n\n"
                    "Please ensure a financial year is open in Financial Year Management.",
                )
                return
        # If period_id is missing, try to determine it from the date incurred
        if existing_period_id is None and existing_fy_id:
            try:
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

        case = {
            "base_transaction_no": dialog_instance.base_transaction_no,
            "date_incurred": str(date_incurred_str),
            "date_identified": str(date_identified_str),
            "date_reported": str(date_reported_str),
            "description": dialog_instance.description_edit.toPlainText().strip(),
            "bas_payment_no": bas_payment_no,
            "bas_payment_date": bas_payment_date_str,
            "bas_journal_no": dialog_instance.bas_journal_no_edit.text().strip(),
            "bas_journal_date": bas_journal_date_str,
            "persal_no": persal_no,
            "category": category_text,
            "responsibility_id": dialog_instance.selected_responsibility_id,
            "amount": amount,
            "source_document": dialog_instance.source_doc_edit.text().strip(),
            "supporting_evidence_path": dialog_instance.supporting_evidence_edit.text().strip(),
            "minutes": dialog_instance.minutes_edit.text().strip(),
            "evidence_path": dialog_instance.assessment_evidence_edit.text().strip(),
            "recovery_evidence_path": dialog_instance.recovery_evidence_edit.text().strip(),
            "criminal_charges": criminal_charges_text,
            "disciplinary_process": disciplinary_text,
            "loss_recovery": loss_recovery_text,
            "prevention_steps": dialog_instance.prevention_steps_edit.toPlainText().strip(),
            "fy_id": existing_fy_id,
            "period_id": existing_period_id,
        }

        # Handle file operations - create case-specific folder structure
        # Optimized file upload: minimize file copying, use efficient database writes
        import time

        upload_start_time = time.time()

        # Temporarily disconnect ALL signals to prevent excessive emissions during upload
        try:
            dialog_instance.category_combo.currentTextChanged.disconnect(
                dialog_instance.schedule_update_conditional_fields
            )
            dialog_instance.assessment_status_combo.currentTextChanged.disconnect(
                dialog_instance.on_assessment_status_changed
            )
            dialog_instance.lc_status_combo.currentTextChanged.disconnect(
                dialog_instance.on_lc_status_changed
            )
            dialog_instance.list_combo.currentTextChanged.disconnect()  # Disconnect any list combo signals
        except TypeError:
            pass  # Signals may not be connected

        year_folder = dialog_instance.create_year_folder(dialog_instance.fy)
        supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
        case_folder = os.path.join(
            supporting_evidence_folder, f"Case {dialog_instance.base_transaction_no}"
        )
        os.makedirs(case_folder, exist_ok=True)

        # Map fields to proper file names
        file_mappings = {
            "source_document": f"{dialog_instance.base_transaction_no} Source Document.pdf",
            "supporting_evidence_path": f"{dialog_instance.base_transaction_no} Supporting Evidence.pdf",
            "minutes": f"{dialog_instance.base_transaction_no} Loss Control Minutes.pdf",
            "evidence_path": f"{dialog_instance.base_transaction_no} Assessment Evidence.pdf",
            "recovery_evidence_path": f"{dialog_instance.base_transaction_no} Recovery Evidence.pdf",
        }

        # Batch file operations for efficiency
        files_to_copy = []
        for field, filename in file_mappings.items():
            if case[field] and case[field].strip():
                source_path = case[field].strip()
                dest_path = os.path.join(case_folder, filename)

                # Check if source and destination are the same
                if os.path.abspath(source_path) == os.path.abspath(dest_path):
                    case[field] = dest_path
                    continue

                if os.path.exists(source_path):
                    # Check if it's a PDF file (only copy PDF files to avoid corruption)
                    if not source_path.lower().endswith(".pdf"):
                        print(
                            f"Warning: Skipping non-PDF file for {field}: {source_path}"
                        )
                        continue

                    files_to_copy.append((field, source_path, dest_path))

        # Perform file copies efficiently
        for field, source_path, dest_path in files_to_copy:
            try:
                # Ensure destination directory exists
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)

                # Check if destination file already exists and is read-only
                if os.path.exists(dest_path):
                    try:
                        # Test if we can write to the file
                        with open(dest_path, "ab") as test_file:
                            pass
                    except PermissionError:
                        QMessageBox.critical(
                            dialog_instance,
                            "File Permission Error",
                            f"Cannot overwrite existing {field} file.\n\n"
                            f"File: {dest_path}\n\n"
                            "The file may be read-only or in use by another program.",
                        )
                        # Reconnect signals before returning
                        dialog_instance.category_combo.currentTextChanged.connect(
                            dialog_instance.schedule_update_conditional_fields
                        )
                        dialog_instance.assessment_status_combo.currentTextChanged.connect(
                            dialog_instance.on_assessment_status_changed
                        )
                        return

                # Try to copy the file (safer than move)
                import shutil

                shutil.copy2(source_path, dest_path)
                case[field] = dest_path

            except PermissionError:
                QMessageBox.critical(
                    dialog_instance,
                    "File Copy Permission Error",
                    f"Cannot copy {field} file due to permission restrictions.\n\n"
                    f"Source: {source_path}\n"
                    f"Destination: {dest_path}\n\n"
                    "Please check file permissions and ensure the source file is not in use.",
                )
                # Reconnect signals before returning
                dialog_instance.category_combo.currentTextChanged.connect(
                    dialog_instance.schedule_update_conditional_fields
                )
                dialog_instance.assessment_status_combo.currentTextChanged.connect(
                    dialog_instance.on_assessment_status_changed
                )
                return
            except OSError as os_error:
                QMessageBox.critical(
                    dialog_instance,
                    "File System Error",
                    f"Failed to copy {field} file due to file system error.\n\n"
                    f"Source: {source_path}\n"
                    f"Destination: {dest_path}\n\n"
                    f"Error: {str(os_error)}",
                )
                # Reconnect signals before returning
                dialog_instance.category_combo.currentTextChanged.connect(
                    dialog_instance.schedule_update_conditional_fields
                )
                dialog_instance.assessment_status_combo.currentTextChanged.connect(
                    dialog_instance.on_assessment_status_changed
                )
                return
            except Exception as copy_error:
                QMessageBox.critical(
                    dialog_instance,
                    "File Copy Error",
                    f"Unexpected error while copying {field} file.\n\n"
                    f"Source: {source_path}\n"
                    f"Destination: {dest_path}\n\n"
                    f"Error: {str(copy_error)}",
                )
        # Reconnect signals after upload
        dialog_instance.category_combo.currentTextChanged.connect(
            dialog_instance.schedule_update_conditional_fields
        )
        dialog_instance.assessment_status_combo.currentTextChanged.connect(
            dialog_instance.on_assessment_status_changed
        )
        dialog_instance.lc_status_combo.currentTextChanged.connect(
            dialog_instance.on_lc_status_changed
        )

        upload_time = time.time() - upload_start_time
        print(
            f"LOG: Uploaded evidence for case {dialog_instance.base_transaction_no} in {upload_time:.2f}s"
        )

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

            cursor.execute(
                """
                    UPDATE cases SET
                        date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                        bas_payment_no = ?, bas_payment_date = ?, bas_journal_no = ?, bas_journal_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                        base_transaction_no = ?, evidence_paths = ?, assessment_status = ?, lc_status = ?, criminal_charges = ?, disciplinary_process = ?,
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
                    if not dialog_instance.handle_case_status_change(
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

                QMessageBox.information(
                    dialog_instance, "Success", "Case updated successfully."
                )

                # Signal parent that case was modified
                dialog_instance.case_modified.emit()

                # Try a different approach - don't call accept() immediately
                # Instead, schedule the dialog to close after a short delay
                from PyQt5.QtCore import QTimer

                def delayed_close():
                    try:
                        dialog_instance.accept()
                    except Exception as delayed_error:
                        try:
                            dialog_instance.done(1)  # Alternative to accept()
                        except Exception as done_error:
                            pass  # Silent failure for dialog closing

                # Schedule the close to happen after current event processing
                QTimer.singleShot(100, delayed_close)

        except Exception as e:
            print(f"DEBUG: Error during database operations: {e}")
            QMessageBox.critical(
                dialog_instance,
                "Database Error",
                f"Failed to save case to database: {str(e)}",
            )
            return
    except Exception as e:

        QMessageBox.critical(dialog_instance, "Error", f"Failed to save case: {str(e)}")

        dialog_instance.reject()


# End of File
