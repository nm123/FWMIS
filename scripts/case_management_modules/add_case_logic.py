import os
import sqlite3
from datetime import datetime

import win32com.client
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox
from scripts.ui.components.add_case_ui import AssessmentDialog
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.contact_utils import get_effective_contacts
from scripts.Utilities.financial_utils import (create_year_folder,
                                               generate_transaction_no,
                                               get_current_open_financial_year,
                                               get_financial_year)
from scripts.Utilities.validation_utils import is_valid_email


class AddCaseLogic:
    def __init__(self, dialog):
        self.dialog = dialog

    def browse_file(self):
        """Browse for a file to attach to the case."""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Select Supporting Evidence", "", "All Files (*.*)"
        )
        if file_path:
            self.dialog.file_path_edit.setText(file_path)

    def browse_source_doc(self):
        """Browse for source document file."""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Select Source Document", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.dialog.source_doc_edit.setText(file_path)

    def browse_minutes(self):
        """Browse for minutes file."""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Select Minutes", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.dialog.minutes_edit.setText(file_path)

    def browse_evidence(self):
        """Browse for evidence file."""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Select Evidence", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.dialog.evidence_edit.setText(file_path)

    def browse_supporting_evidence(self):
        """Browse for supporting evidence file."""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Select Supporting Evidence", "", "All Files (*.*)"
        )
        if file_path:
            self.dialog.supporting_evidence_edit.setText(file_path)

    def select_responsibility(self):
        from scripts.case_management_modules.responsibility_selection import \
            ResponsibilitySelectionDialog

        dialog = ResponsibilitySelectionDialog(self.dialog)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.dialog.responsibility_edit.setText(selected["name"])
                self.dialog.selected_responsibility_id = selected["id"]

    def on_status_changed(self, status):
        """Handle status selection change with special logic for Valid and Confirmed statuses"""
        if status == "Valid":
            # Show warning dialog for Valid status
            reply = QMessageBox.question(
                self.dialog,
                "Confirm Valid Status",
                "Selecting 'Valid' means this case is NOT Fruitless and Wasteful Expenditure.\n\n"
                "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
                "This will finalise the case.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.dialog.supporting_evidence_compulsory = True
                # Update the label to show it's compulsory
                self.dialog.file_path_edit.setPlaceholderText(
                    "Assessment Evidence is REQUIRED - Select file..."
                )
            else:
                # Revert to previous status or default
                self.dialog.status_combo.setCurrentText("Alleged")
                self.dialog.supporting_evidence_compulsory = False
                self.dialog.file_path_edit.setPlaceholderText("Select file...")
        elif status == "Confirmed":
            # Show warning dialog for Confirmed status
            reply = QMessageBox.question(
                self.dialog,
                "Confirm Confirmed Status",
                "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
                "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
                "The case will be copied to the Lead Schedule.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.dialog.supporting_evidence_compulsory = True
                # Update the label to show it's compulsory
                self.dialog.file_path_edit.setPlaceholderText(
                    "Assessment Evidence is REQUIRED - Select file..."
                )
            else:
                # Revert to previous status or default
                self.dialog.status_combo.setCurrentText("Alleged")
                self.dialog.supporting_evidence_compulsory = False
                self.dialog.file_path_edit.setPlaceholderText("Select file...")
        else:
            # Reset the compulsory flag for other statuses
            self.dialog.supporting_evidence_compulsory = False
            self.dialog.file_path_edit.setPlaceholderText("Select file...")

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        # Ensure list combo has items before accessing currentText
        if self.dialog.list_combo.count() == 0:
            return

        selected_list = self.dialog.list_combo.currentText()

        # Store current status before clearing
        current_status = (
            self.dialog.status_combo.currentText()
            if self.dialog.status_combo.count() > 0
            else "Alleged"
        )

        # Update status options based on list selection
        self.dialog.status_combo.clear()

        if selected_list == "Lead Schedule":
            # For Lead Schedule, include additional statuses
            self.dialog.status_combo.addItems(
                [
                    "Alleged",
                    "Under Assessment",
                    "Valid",
                    "Confirmed",
                    "Recovered",
                    "Write Off Recommended",
                ]
            )
        else:
            # For Checklist and other lists, show standard statuses
            self.dialog.status_combo.addItems(
                ["Alleged", "Under Assessment", "Valid", "Confirmed"]
            )

        # Try to restore the previous selection if it's still valid
        if current_status in [
            self.dialog.status_combo.itemText(i)
            for i in range(self.dialog.status_combo.count())
        ]:
            self.dialog.status_combo.setCurrentText(current_status)
        else:
            self.dialog.status_combo.setCurrentText("Alleged")

        # Get the selected status after updating options
        selected_status = self.dialog.status_combo.currentText()

        # Show assessment fields only for Lead Schedule + Valid/Confirmed status
        show_assessment_fields = (
            selected_list == "Lead Schedule"
            and selected_status in ["Valid", "Confirmed"]
        )

        # Update visibility of assessment-related fields
        self.dialog.source_doc_label.setVisible(show_assessment_fields)
        self.dialog.source_doc_edit.setVisible(show_assessment_fields)
        self.dialog.source_doc_button.setVisible(show_assessment_fields)

        self.dialog.minutes_label.setVisible(show_assessment_fields)
        self.dialog.minutes_edit.setVisible(show_assessment_fields)
        self.dialog.minutes_button.setVisible(show_assessment_fields)

        self.dialog.evidence_label.setVisible(show_assessment_fields)
        self.dialog.evidence_edit.setVisible(show_assessment_fields)
        self.dialog.evidence_button.setVisible(show_assessment_fields)

        self.dialog.assessed_by_label.setVisible(show_assessment_fields)
        self.dialog.assessed_by_edit.setVisible(show_assessment_fields)

        self.dialog.assessment_date_label.setVisible(show_assessment_fields)
        self.dialog.assessment_date_edit.setVisible(show_assessment_fields)

        # Update compulsory fields based on category
        selected_category = (
            self.dialog.category_combo.currentText()
            if self.dialog.category_combo.count() > 0
            else ""
        )
        if selected_category:
            category = next(
                (c for c in self.dialog.categories if c["name"] == selected_category),
                None,
            )
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)
            else:
                bas_comp = False
                persal_comp = False
        else:
            bas_comp = False
            persal_comp = False

        # Update BAS fields
        self.dialog.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
        self.dialog.bas_label.setVisible(bas_comp)
        self.dialog.bas_payment_no_edit.setVisible(bas_comp)
        self.dialog.bas_date_label.setText(
            "BAS Payment Date:" + (" *" if bas_comp else "")
        )
        self.dialog.bas_date_label.setVisible(bas_comp)
        self.dialog.bas_payment_date_edit.setVisible(bas_comp)

        # Update BAS Journal fields
        self.dialog.bas_journal_label.setText(
            "BAS Journal No:" + (" *" if bas_comp else "")
        )
        self.dialog.bas_journal_label.setVisible(bas_comp)
        self.dialog.bas_journal_no_edit.setVisible(bas_comp)
        self.dialog.bas_journal_date_label.setText(
            "BAS Journal Date:" + (" *" if bas_comp else "")
        )
        self.dialog.bas_journal_date_label.setVisible(bas_comp)
        self.dialog.bas_journal_date_edit.setVisible(bas_comp)

        # Update Persal field
        self.dialog.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
        self.dialog.persal_label.setVisible(persal_comp)
        self.dialog.persal_no_edit.setVisible(persal_comp)

    def save_case(self):
        from scripts.Utilities.add_case_utils import (get_case_data,
                                                      handle_file_operations,
                                                      validate_add_data)

        try:
            # Validate data
            if not validate_add_data(self.dialog):
                return

            # Generate transaction number
            self.dialog.transaction_no = generate_transaction_no(self.dialog.fy)
            self.dialog.trans_no_edit.setText(self.dialog.transaction_no)

            # Get case data
            case = get_case_data(self.dialog)

            # Get current financial year ID
            current_fy = get_current_open_financial_year()
            fy_id = current_fy[0] if current_fy else None

            if fy_id is None:
                QMessageBox.critical(
                    self.dialog,
                    "Financial Year Error",
                    "Cannot save case: No open financial year found.\n\n"
                    "Please ensure a financial year is open in Financial Year Management.",
                )
                return

            # Get period ID for the transaction date
            period_id = None
            if fy_id:
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
                        (fy_id, case["date_incurred"], case["date_incurred"]),
                    )
                    period_result = cursor_temp.fetchone()
                    period_id = period_result[0] if period_result else None

                    conn_temp.close()
                except Exception as e:
                    print(f"Warning: Could not determine period ID: {e}")
                    period_id = None

            case["fy_id"] = fy_id
            case["period_id"] = period_id

            # Handle file operations
            if not handle_file_operations(
                case, self.dialog.fy, self.dialog.transaction_no
            ):
                return

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO cases (
                    transaction_no, base_transaction_no, date_incurred, date_identified, date_reported,
                    description, bas_payment_no, bas_payment_date, persal_no, category,
                    responsibility_id, amount, source_document, minutes, evidence_path,
                    status, list, assessment_assessed_by, assessment_date, assessment_result,
                    fy_id, period_id, criminal_charges, disciplinary_process, loss_recovery,
                    prevention_steps, original_list, attachments, shared_document_id, bas_journal_no, bas_journal_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case["transaction_no"],
                    case["transaction_no"],
                    case["date_incurred"],
                    case["date_identified"],
                    case["date_reported"],
                    case["description"],
                    case["bas_payment_no"],
                    case["bas_payment_date"],
                    case["persal_no"],
                    case["category"],
                    case["responsibility_id"],
                    case["amount"],
                    case["source_document"],
                    case["minutes"],
                    case["evidence_path"],
                    case["status"],
                    case["list"],
                    case["assessment_assessed_by"],
                    case["assessment_date"],
                    case["assessment_result"],
                    case["fy_id"],
                    case["period_id"],
                    "N/A",
                    "N/A",
                    "N/A",
                    case["prevention_steps"],
                    case["original_list"],
                    case["attachments"],
                    None,
                    case["bas_journal_no"],
                    case["bas_journal_date"],
                ),
            )

            conn.commit()
            case_id = cursor.lastrowid

            # Check if supporting evidence is missing
            if not case["supporting_evidence_path"]:
                # Update status to indicate missing supporting evidence
                conn.execute(
                    "UPDATE cases SET status = ? WHERE transaction_no = ?",
                    ("Missing Supporting Evidence", self.dialog.transaction_no),
                )
                conn.commit()
                QMessageBox.warning(
                    self.dialog,
                    "Supporting Evidence Missing",
                    "Case saved successfully, but Supporting Evidence (To prove Existence) is missing.\n\n"
                    "This case has been added to the To-Do List for follow-up.",
                )
            else:
                QMessageBox.information(
                    self.dialog, "Success", "Case added successfully."
                )

            conn.close()

            # Log audit trail
            save_audit_log(
                "add_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": self.dialog.transaction_no,
                    "details": case,
                },
                self.dialog.fy,
            )

            self.reset_form_for_next_case()

        except Exception as e:
            QMessageBox.critical(self.dialog, "Error", f"Failed to save case: {str(e)}")
            self.dialog.reject()

    def save_case_and_close(self):
        """Save the case and close the dialog"""
        self.save_case()
        self.dialog.accept()

    def reset_form_for_next_case(self):
        """Reset the form for entering the next case"""
        from scripts.Utilities.add_case_utils import reset_form_fields

        reset_form_fields(self.dialog)

    def next_case(self):
        # Generate new transaction number for next case
        self.dialog.transaction_no = generate_transaction_no(self.dialog.fy)
        self.dialog.trans_no_edit.setText(self.dialog.transaction_no)
        self.dialog.description_edit.clear()
        self.dialog.bas_payment_no_edit.clear()
        self.dialog.bas_journal_no_edit.clear()
        self.dialog.persal_no_edit.clear()
        self.dialog.amount_edit.clear()
        self.dialog.evidence_edit.clear()
        self.dialog.prevention_steps_edit.clear()
        # Always reset list combo to Checklist
        if "Checklist" in [
            l["name"]
            for l in self.dialog.lists
            if l.get("is_system", False) and l["name"] != "Deleted Cases"
        ]:
            self.dialog.list_combo.setCurrentText("Checklist")

        # Reset supporting evidence compulsory flag
        self.dialog.supporting_evidence_compulsory = False
        self.dialog.file_path_edit.setPlaceholderText("Select file...")

    def send_reminder_email(self):
        if not self.dialog.selected_responsibility_id:
            QMessageBox.warning(
                self.dialog,
                "No Responsibility",
                "Please select a responsibility first.",
            )
            return
        resp_id = self.dialog.selected_responsibility_id
        contacts = get_effective_contacts(self.dialog.responsibilities, resp_id)
        emails = [c["email"] for c in contacts if is_valid_email(c["email"])]
        if not emails:
            QMessageBox.warning(
                self.dialog,
                "No Contacts",
                "No valid email contacts found for this responsibility.",
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT body FROM email_templates WHERE name = ?",
            ("Reminder - Assessment Evidence",),
        )
        template = cursor.fetchone()
        conn.close()

        if not template:
            QMessageBox.warning(self.dialog, "No Template", "No email template found.")
            return

        body = template[0]
        body = body.replace("[Recipient]", ", ".join(c["name"] for c in contacts))
        body = body.replace("[Case ID]", self.dialog.transaction_no)
        body = body.replace(
            "[Due Date]", QDate.currentDate().addDays(7).toString("yyyy-MM-dd")
        )
        body = body.replace("[Contact Email]", ", ".join(emails))
        body = body.replace("[Your Name]", "Accounts Payable Team")

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(emails)
        mail.Subject = (
            f"Reminder: Assessment Evidence for Case {self.dialog.transaction_no}"
        )
        mail.Body = body
        mail.Display()

    def open_assessment(self):
        if not self.dialog.evidence_edit.text():
            QMessageBox.warning(
                self.dialog, "No Evidence", "Please upload evidence before assessment."
            )
            return
        dialog = AssessmentDialog(self.dialog)
        if dialog.exec_():
            assessment_data = dialog.get_assessment_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM cases")
            max_id = cursor.fetchone()[0]
            case_id = (max_id or 0) + 1
            cursor.execute(
                "UPDATE cases SET assessment_assessed_by = ?, assessment_date = ?, assessment_result = ?, status = ?, list = ? WHERE transaction_no = ?",
                (
                    assessment_data["assessed_by"],
                    assessment_data["assessment_date"],
                    assessment_data["result"],
                    assessment_data["result"],
                    "Lead Schedule",
                    self.dialog.transaction_no,
                ),
            )
            conn.commit()
            conn.close()
            save_audit_log(
                "assess_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": self.dialog.transaction_no,
                    "details": assessment_data,
                },
                self.dialog.fy,
            )
