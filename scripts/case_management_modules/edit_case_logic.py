import os
import shutil
import sqlite3
from datetime import datetime

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (create_year_folder,
                                               get_financial_year)


class EditCaseLogic:
    def __init__(self, dialog):
        self.dialog = dialog
        self.fy = dialog.fy
        self.transaction_no = dialog.transaction_no
        self.case_data = dialog.case_data

    def load_case_data(self):
        """Load existing case data into the form fields"""
        # Set responsibility
        resp = next(
            (r for r in self.dialog.responsibilities if r["id"] == self.case_data[10]),
            None,
        )
        if resp:
            self.dialog.responsibility_edit.setText(resp["name"])

        # Set dates
        if self.case_data[2]:  # date_incurred
            self.dialog.date_incurred_edit.setDate(
                QDate.fromString(self.case_data[2], "yyyy-MM-dd")
            )
        if self.case_data[3]:  # date_identified
            self.dialog.date_identified_edit.setDate(
                QDate.fromString(self.case_data[3], "yyyy-MM-dd")
            )
        if self.case_data[4]:  # date_reported
            self.dialog.date_reported_edit.setDate(
                QDate.fromString(self.case_data[4], "yyyy-MM-dd")
            )

        # Set description
        if self.case_data[5]:  # description
            self.dialog.description_edit.setPlainText(self.case_data[5])

        # Set category
        if self.case_data[9]:  # category
            self.dialog.category_combo.setCurrentText(self.case_data[9])

        # Set list
        if self.case_data[16]:  # list
            self.dialog.list_combo.setCurrentText(self.case_data[16])

        # Set status
        if self.case_data[17]:  # status
            self.dialog.status_combo.setCurrentText(self.case_data[17])

        # Set criminal charges
        if len(self.case_data) > 22 and self.case_data[22]:
            self.dialog.criminal_charges_combo.setCurrentText(self.case_data[22])

        # Set disciplinary
        if len(self.case_data) > 23 and self.case_data[23]:
            self.dialog.disciplinary_combo.setCurrentText(self.case_data[23])

        # Set loss recovery
        if len(self.case_data) > 24 and self.case_data[24]:
            self.dialog.loss_recovery_combo.setCurrentText(self.case_data[24])

        # Set prevention steps
        if len(self.case_data) > 25 and self.case_data[25]:
            self.dialog.prevention_steps_edit.setPlainText(self.case_data[25])

        # Set amount
        if self.case_data[11]:  # amount
            self.dialog.amount_edit.setText(str(self.case_data[11]))

        # Set BAS fields
        if self.case_data[6]:  # bas_payment_no
            self.dialog.bas_payment_no_edit.setText(self.case_data[6])
        if self.case_data[7]:  # bas_payment_date
            self.dialog.bas_payment_date_edit.setDate(
                QDate.fromString(self.case_data[7], "yyyy-MM-dd")
            )

        # Set Persal No
        if self.case_data[8]:  # persal_no
            self.dialog.persal_no_edit.setText(self.case_data[8])

        # Set file paths
        if self.case_data[12]:  # source_document
            self.dialog.source_doc_edit.setText(self.case_data[12])
        if self.case_data[13]:  # minutes
            self.dialog.minutes_edit.setText(self.case_data[13])
        if self.case_data[14]:  # evidence_path
            self.dialog.evidence_edit.setText(self.case_data[14])

        # Set assessment fields
        if len(self.case_data) > 18 and self.case_data[18]:  # assessment_assessed_by
            self.dialog.assessed_by_edit.setText(self.case_data[18])
        if len(self.case_data) > 19 and self.case_data[19]:  # assessment_date
            self.dialog.assessment_date_edit.setDate(
                QDate.fromString(self.case_data[19], "yyyy-MM-dd")
            )

    def save_case(self) -> None:
        """Save the case data to database"""
        try:
            bas_payment_no = self.dialog.bas_payment_no_edit.text().strip()
            persal_no = self.dialog.persal_no_edit.text().strip()
            amount_text = self.dialog.amount_edit.text().strip()

            # Get compulsory settings from selected category
            category_name = self.dialog.category_combo.currentText()
            category = next(
                (c for c in self.dialog.categories if c["name"] == category_name), None
            )
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)
            else:
                bas_comp = False
                persal_comp = False

            # Check compulsory fields
            missing_fields = []
            if bas_comp and not bas_payment_no:
                missing_fields.append("BAS Payment No")
            if persal_comp and not persal_no:
                missing_fields.append("Persal No")
            if not amount_text:
                missing_fields.append("Amount")

            if missing_fields:
                QMessageBox.warning(
                    self.dialog,
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
                    self.dialog, "Invalid Input", "Amount must be a positive number."
                )
                return

            if not self.dialog.selected_responsibility_id:
                QMessageBox.warning(
                    self.dialog, "Invalid Input", "Please select a responsibility."
                )
                return

            # Validate supporting evidence if compulsory
            if (
                self.dialog.supporting_evidence_compulsory
                and not self.dialog.evidence_edit.text().strip()
            ):
                QMessageBox.warning(
                    self.dialog,
                    "Supporting Evidence Required",
                    "Supporting Evidence is compulsory for Valid status cases.\n\n"
                    "Please select a file before saving.",
                )
                return

            # Convert dates
            date_incurred_str = self.dialog.date_incurred_edit.date().toString(
                "yyyy-MM-dd"
            )
            date_identified_str = self.dialog.date_identified_edit.date().toString(
                "yyyy-MM-dd"
            )
            date_reported_str = self.dialog.date_reported_edit.date().toString(
                "yyyy-MM-dd"
            )
            bas_payment_date_str = self.dialog.bas_payment_date_edit.date().toString(
                "yyyy-MM-dd"
            )
            assessment_date_str = self.dialog.assessment_date_edit.date().toString(
                "yyyy-MM-dd"
            )

            # Create case dictionary
            category_text = self.dialog.category_combo.currentText()
            status_text = self.dialog.status_combo.currentText()
            list_text = self.dialog.list_combo.currentText()
            criminal_charges_text = self.dialog.criminal_charges_combo.currentText()
            disciplinary_text = self.dialog.disciplinary_combo.currentText()
            loss_recovery_text = self.dialog.loss_recovery_combo.currentText()

            # Get existing fy_id and period_id
            existing_fy_id = self.case_data[21] if len(self.case_data) > 21 else None
            existing_period_id = (
                self.case_data[22] if len(self.case_data) > 22 else None
            )

            # Fix fy_id if missing
            if existing_fy_id is None:
                from scripts.Utilities.financial_utils import \
                    get_current_open_financial_year

                current_fy = get_current_open_financial_year()
                if current_fy:
                    existing_fy_id = current_fy[0]
                else:
                    QMessageBox.critical(
                        self.dialog,
                        "Financial Year Error",
                        "Cannot save case: No open financial year found.\n\n"
                        "Please ensure a financial year is open in Financial Year Management.",
                    )
                    return

            # Fix period_id if missing
            if existing_period_id is None and existing_fy_id:
                conn_temp = sqlite3.connect(DB_PATH)
                cursor_temp = conn_temp.cursor()
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

            # Handle transaction_no suffix changes
            base_transaction_no = self.transaction_no
            has_ls = base_transaction_no.endswith(
                "-LS"
            )  # New flag to track if original had -LS
            if base_transaction_no.endswith("-LS"):
                base_transaction_no = base_transaction_no[:-3]
            elif base_transaction_no.endswith("-WOR"):
                base_transaction_no = base_transaction_no[:-4]

            transaction_no_with_suffix = base_transaction_no
            if status_text == "Confirmed":
                transaction_no_with_suffix = f"{base_transaction_no}-LS"
                list_text = "Lead Schedule"
            elif status_text == "Write Off Recommended":
                if (
                    has_ls
                ):  # If original had -LS, preserve it for Lead Schedule visibility
                    transaction_no_with_suffix = f"{base_transaction_no}-LS-WOR"
                else:
                    transaction_no_with_suffix = f"{base_transaction_no}-WOR"
                list_text = "Write-Off Recommended"
            else:
                list_text = "Checklist"

            print(
                f"Updated transaction_no: {transaction_no_with_suffix}, has_ls: {has_ls}"
            )

            case = {
                "transaction_no": transaction_no_with_suffix,
                "date_incurred": date_incurred_str,
                "date_identified": date_identified_str,
                "date_reported": date_reported_str,
                "description": self.dialog.description_edit.toPlainText().strip(),
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": bas_payment_date_str,
                "persal_no": persal_no,
                "category": category_text,
                "responsibility_id": self.dialog.selected_responsibility_id,
                "amount": amount,
                "source_document": self.dialog.source_doc_edit.text().strip(),
                "minutes": self.dialog.minutes_edit.text().strip(),
                "evidence_path": self.dialog.evidence_edit.text().strip(),
                "attachments": "[]",
                "status": status_text,
                "list": list_text,
                "assessment_assessed_by": self.dialog.assessed_by_edit.text().strip(),
                "assessment_date": assessment_date_str,
                "assessment_result": "",
                "criminal_charges": criminal_charges_text,
                "disciplinary_process": disciplinary_text,
                "loss_recovery": loss_recovery_text,
                "prevention_steps": self.dialog.prevention_steps_edit.toPlainText().strip(),
                "fy_id": existing_fy_id,
                "period_id": existing_period_id,
                "original_list": list_text,
            }

            # Handle file operations
            year_folder = create_year_folder(self.fy)
            supporting_evidence_folder = os.path.join(
                year_folder, "Supporting Evidence"
            )
            case_folder = os.path.join(
                supporting_evidence_folder, f"Case {self.transaction_no}"
            )
            os.makedirs(case_folder, exist_ok=True)

            file_mappings = {
                "source_document": f"{self.transaction_no} Source Document.pdf",
                "minutes": f"{self.transaction_no} Loss Control Minutes.pdf",
                "evidence_path": f"{self.transaction_no} Assessment Evidence.pdf",
            }

            for field, filename in file_mappings.items():
                if case[field] and case[field].strip():
                    source_path = case[field].strip()
                    dest_path = os.path.join(case_folder, filename)

                    if os.path.abspath(source_path) == os.path.abspath(dest_path):
                        case[field] = dest_path
                        continue

                    if os.path.exists(source_path):
                        if not source_path.lower().endswith(".pdf"):
                            continue
                        try:
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            shutil.copy2(source_path, dest_path)
                            case[field] = dest_path
                        except Exception as e:
                            QMessageBox.warning(
                                self.dialog,
                                "File Save Error",
                                f"Failed to save {field} file: {str(e)}",
                            )
                            return
                    else:
                        QMessageBox.warning(
                            self.dialog,
                            "File Not Found",
                            f"The selected {field} file could not be found: {source_path}",
                        )
                        return

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE cases SET
                    transaction_no = ?, date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                    bas_payment_no = ?, bas_payment_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                    source_document = ?, minutes = ?, evidence_path = ?, attachments = ?, status = ?, list = ?, assessment_assessed_by = ?,
                    assessment_date = ?, assessment_result = ?, fy_id = ?, period_id = ?, criminal_charges = ?, disciplinary_process = ?,
                    loss_recovery = ?, prevention_steps = ?, original_list = ?
                WHERE transaction_no = ?
            """,
                (
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
                    case["attachments"],
                    case["status"],
                    case["list"],
                    case["assessment_assessed_by"],
                    case["assessment_date"],
                    case["assessment_result"],
                    case["fy_id"],
                    case["period_id"],
                    case["criminal_charges"],
                    case["disciplinary_process"],
                    case["loss_recovery"],
                    case["prevention_steps"],
                    case["original_list"],
                    self.transaction_no,
                ),
            )

            conn.commit()
            case_id = self.case_data[0]
            conn.close()

            assert transaction_no_with_suffix.endswith(("-LS", "-WOR", "-LS-WOR", ""))

            save_audit_log(
                "edit_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": self.transaction_no,
                    "details": case,
                },
                self.fy,
            )

            QMessageBox.information(
                self.dialog, "Success", "Case updated successfully."
            )
            self.dialog.accept()

        except Exception as e:
            QMessageBox.critical(self.dialog, "Error", f"Failed to save case: {str(e)}")
            self.dialog.reject()

    def delete_case(self):
        """Delete case by moving it to Deleted Cases"""
        reply = QMessageBox.question(
            self.dialog,
            "Confirm Delete",
            f"Are you sure you want to delete case {self.transaction_no}?\n\n"
            "This will move the case to the Deleted Cases list.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get current list before updating
                cursor.execute(
                    "SELECT list FROM cases WHERE transaction_no = ?",
                    (self.transaction_no,),
                )
                current_list_result = cursor.fetchone()
                current_list = (
                    current_list_result[0] if current_list_result else "Unknown"
                )

                # Update case to Deleted Cases
                cursor.execute(
                    """
                    UPDATE cases
                    SET list = 'Deleted Cases', original_list = ?
                    WHERE transaction_no = ?
                """,
                    (current_list, self.transaction_no),
                )

                conn.commit()
                conn.close()

                # Log audit trail
                save_audit_log(
                    "delete_case",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "case_id": self.case_data[0],
                        "transaction_no": self.transaction_no,
                        "original_list": current_list,
                        "details": "Case moved to Deleted Cases",
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self.dialog,
                    "Success",
                    f"Case {self.transaction_no} has been moved to Deleted Cases.",
                )
                self.dialog.accept()

            except Exception as e:
                QMessageBox.critical(
                    self.dialog, "Error", f"Failed to delete case: {str(e)}"
                )
