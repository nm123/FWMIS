import json
import sqlite3
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QMessageBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget, QTabWidget)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.annexure_utils import get_all_annexures, get_annexure_details
from scripts.Utilities.excel_exporter import export_annexure_to_excel
from scripts.Utilities.pdf_exporter import export_annexure_to_pdf


class WriteOffManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Write-Off Annexure Log")
        self.setFixedSize(1200, 800)
        self.fy = get_financial_year()
        self.setup_ui()
        self.load_annexures()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # FY Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Financial Year:"))

        self.fy_filter_combo = QComboBox()
        self.fy_filter_combo.setFixedWidth(200)
        self.load_fy_filter()
        self.fy_filter_combo.currentTextChanged.connect(self.load_annexures)
        filter_layout.addWidget(self.fy_filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Create tab widget (removed - now single view)
        # self.tab_widget = QTabWidget()

        # Annexures content directly in main layout
        annexures_group = QGroupBox("Write-Off Annexures")
        annexures_group_layout = QVBoxLayout(annexures_group)

        self.annexures_table = QTableWidget()
        self.annexures_table.setColumnCount(8)
        self.annexures_table.setHorizontalHeaderLabels(
            [
                "Annexure ID",
                "Created Date",
                "Status",
                "Cases",
                "Total Amount",
                "Actions",
                "Details",
                "Export",
            ]
        )

        # Set column widths
        header = self.annexures_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.annexures_table.setColumnWidth(0, 120)  # Annexure ID
        self.annexures_table.setColumnWidth(1, 120)  # Created Date
        self.annexures_table.setColumnWidth(2, 100)  # Status
        self.annexures_table.setColumnWidth(3, 80)  # Cases
        self.annexures_table.setColumnWidth(4, 120)  # Total Amount
        self.annexures_table.setColumnWidth(5, 200)  # Actions
        self.annexures_table.setColumnWidth(6, 150)  # Details
        self.annexures_table.setColumnWidth(7, 150)  # Export

        annexures_group_layout.addWidget(self.annexures_table)
        layout.addWidget(annexures_group)

        # Annexures action buttons
        annexures_btn_layout = QHBoxLayout()
        refresh_annexures_btn = QPushButton("Refresh Annexures")
        refresh_annexures_btn.clicked.connect(self.load_annexures)
        annexures_btn_layout.addWidget(refresh_annexures_btn)
        annexures_btn_layout.addStretch()
        layout.addLayout(annexures_btn_layout)

    def load_fy_filter(self):
        """Load financial years into the filter combo."""
        try:
            from scripts.Utilities.financial_utils import get_all_financial_years
            financial_years = get_all_financial_years()

            self.fy_filter_combo.clear()
            self.fy_filter_combo.addItem("All Years", None)

            for fy_id, fy_string, is_open in financial_years:
                display_text = f"{fy_string}"
                if is_open:
                    display_text += " (Current)"
                self.fy_filter_combo.addItem(display_text, fy_id)

            # Default to current FY
            current_fy = get_financial_year()
            for i in range(self.fy_filter_combo.count()):
                if self.fy_filter_combo.itemData(i) and f"{current_fy.split('-')[0]}-{current_fy.split('-')[1]}" in self.fy_filter_combo.itemText(i):
                    self.fy_filter_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            print(f"Error loading FY filter: {e}")
            self.fy_filter_combo.addItem("All Years", None)

    def load_submissions(self):
        """Load write-off submissions from database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, submission_id, created_date, status, case_ids, total_amount, notes
                FROM write_off_submissions
                ORDER BY created_date DESC
            """
            )

            submissions = cursor.fetchall()
            self.submissions_table.setRowCount(len(submissions))

            for row, submission in enumerate(submissions):
                (
                    sub_id,
                    submission_id,
                    created_date,
                    status,
                    case_ids_json,
                    total_amount,
                    notes,
                ) = submission

                # Basic info
                self.submissions_table.setItem(row, 0, QTableWidgetItem(submission_id))
                self.submissions_table.setItem(row, 1, QTableWidgetItem(created_date))
                self.submissions_table.setItem(row, 2, QTableWidgetItem(status))

                # Cases count
                try:
                    case_ids = json.loads(case_ids_json) if case_ids_json else []
                    self.submissions_table.setItem(
                        row, 3, QTableWidgetItem(str(len(case_ids)))
                    )
                except Exception as e:
                    self.submissions_table.setItem(row, 3, QTableWidgetItem("0"))

                # Total amount
                amount_item = format_currency_amount(total_amount, right_align=True)
                self.submissions_table.setItem(row, 4, amount_item)

                # Actions button
                actions_widget = self.create_actions_widget(
                    sub_id, submission_id, status
                )
                self.submissions_table.setCellWidget(row, 5, actions_widget)

                # Details button
                details_btn = QPushButton("View Details")
                details_btn.clicked.connect(
                    lambda checked, s_id=sub_id: self.view_submission_details(s_id)
                )
                self.submissions_table.setCellWidget(row, 6, details_btn)

                # Store submission data
                self.submissions_table.item(row, 0).setData(Qt.UserRole, sub_id)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load submissions: {str(e)}")
        finally:
            conn.close()

    def create_actions_widget(self, submission_id, submission_code, status):
        """Create action buttons widget for a submission"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        if status == "Draft":
            submit_btn = QPushButton("Submit")
            submit_btn.clicked.connect(
                lambda: self.submit_submission(submission_id, submission_code)
            )
            layout.addWidget(submit_btn)

        elif status == "Submitted":
            approve_btn = QPushButton("Approve")
            approve_btn.clicked.connect(
                lambda: self.approve_submission(submission_id, submission_code)
            )
            approve_btn.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; }"
            )
            layout.addWidget(approve_btn)

            reject_btn = QPushButton("Reject")
            reject_btn.clicked.connect(
                lambda: self.reject_submission(submission_id, submission_code)
            )
            reject_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; }"
            )
            layout.addWidget(reject_btn)

        layout.addStretch()
        return widget

    def submit_submission(self, submission_id, submission_code):
        """Submit a draft submission for approval"""
        reply = QMessageBox.question(
            self,
            "Submit Submission",
            f"Are you sure you want to submit write-off submission {submission_code} for approval?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE write_off_submissions
                    SET status = 'Submitted', submitted_date = ?
                    WHERE id = ?
                """,
                    (datetime.now().strftime("%Y-%m-%d"), submission_id),
                )

                conn.commit()

                # Log audit trail
                save_audit_log(
                    "write_off_submission_submitted",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "submission_id": submission_code,
                        "submission_db_id": submission_id,
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"Submission {submission_code} has been submitted for approval.",
                )
                self.load_submissions()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to submit submission: {str(e)}"
                )
            finally:
                conn.close()

    def approve_submission(self, submission_id, submission_code):
        """Approve a submitted write-off submission"""
        reply = QMessageBox.question(
            self,
            "Approve Submission",
            f"Are you sure you want to approve write-off submission {submission_code}?\n\n"
            "This will write off all cases in the submission.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get submission details
                cursor.execute(
                    "SELECT case_ids FROM write_off_submissions WHERE id = ?",
                    (submission_id,),
                )
                result = cursor.fetchone()

                if result:
                    case_ids_json = result[0]
                    try:
                        case_ids = json.loads(case_ids_json) if case_ids_json else []

                        # Update submission status
                        cursor.execute(
                            """
                            UPDATE write_off_submissions
                            SET status = 'Approved', approved_date = ?
                            WHERE id = ?
                        """,
                            (datetime.now().strftime("%Y-%m-%d"), submission_id),
                        )

                        # Write off all cases in the submission
                        for case_id in case_ids:
                            cursor.execute(
                                """
                                UPDATE cases
                                SET status = 'Written Off', list = 'Written Off',
                                    is_finalized = 1, finalized_date = ?, finalization_reason = ?
                                WHERE id = ?
                            """,
                                (
                                    datetime.now().strftime("%Y-%m-%d"),
                                    "Write-off approved",
                                    case_id,
                                ),
                            )

                        conn.commit()

                        # Log audit trail
                        save_audit_log(
                            "write_off_submission_approved",
                            {
                                "timestamp": datetime.now().isoformat(),
                                "submission_id": submission_code,
                                "submission_db_id": submission_id,
                                "cases_written_off": case_ids,
                            },
                            self.fy,
                        )

                        QMessageBox.information(
                            self,
                            "Success",
                            f"Submission {submission_code} approved!\n"
                            f"{len(case_ids)} cases have been written off.",
                        )
                        self.load_submissions()

                    except json.JSONDecodeError:
                        QMessageBox.critical(
                            self, "Error", "Invalid case IDs in submission."
                        )

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to approve submission: {str(e)}"
                )
            finally:
                conn.close()

    def reject_submission(self, submission_id, submission_code):
        """Reject a submitted write-off submission"""
        # Could add a reason dialog here
        reply = QMessageBox.question(
            self,
            "Reject Submission",
            f"Are you sure you want to reject write-off submission {submission_code}?\n\n"
            "The submission will be returned to draft status.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE write_off_submissions
                    SET status = 'Rejected'
                    WHERE id = ?
                """,
                    (submission_id,),
                )

                conn.commit()

                # Log audit trail
                save_audit_log(
                    "write_off_submission_rejected",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "submission_id": submission_code,
                        "submission_db_id": submission_id,
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self, "Success", f"Submission {submission_code} has been rejected."
                )
                self.load_submissions()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to reject submission: {str(e)}"
                )
            finally:
                conn.close()

    def view_submission_details(self, submission_id):
        """View detailed information about a submission"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT ws.submission_id, ws.created_date, ws.status, ws.case_ids,
                       ws.total_amount, ws.notes, c.transaction_no, c.category, c.determination_amount
                FROM write_off_submissions ws
                LEFT JOIN cases c ON c.write_off_submission_id = ws.submission_id
                WHERE ws.id = ?
            """,
                (submission_id,),
            )

            results = cursor.fetchall()

            if results:
                submission_code = results[0][0]
                created_date = results[0][1]
                status = results[0][2]
                total_amount = results[0][4]
                notes = results[0][5]

                # Build details message
                details = f"Submission: {submission_code}\n"
                details += f"Created: {created_date}\n"
                details += f"Status: {status}\n"
                details += (
                    f"Total Cases: {len([r for r in results if r[6] is not None])}\n"
                )
                details += f"Total Amount: {format_currency_amount(total_amount)}\n\n"

                if notes:
                    details += f"Notes: {notes}\n\n"

                details += "Cases in Submission:\n"
                for result in results:
                    if result[6]:  # transaction_no
                        details += f"  - {result[6]} ({result[7] or 'N/A'}): {format_currency_amount(result[8] or 0)}\n"

                QMessageBox.information(self, "Submission Details", details)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load submission details: {str(e)}"
            )
        finally:
            conn.close()

    def load_annexures(self):
        """Load write-off annexures from database with FY filtering"""
        try:
            # Get selected FY filter
            selected_fy_id = self.fy_filter_combo.currentData()

            # Get annexures (modify get_all_annexures to accept FY filter)
            annexures = get_all_annexures(fy_id=selected_fy_id)
            self.annexures_table.setRowCount(len(annexures))

            for row, annexure in enumerate(annexures):
                # Annexure No
                self.annexures_table.setItem(row, 0, QTableWidgetItem(annexure['annexure_no']))
                
                # Role
                self.annexures_table.setItem(row, 1, QTableWidgetItem(annexure['role']))
                
                # Created Date
                created_date = annexure['created_at'][:10] if annexure['created_at'] else ""
                self.annexures_table.setItem(row, 2, QTableWidgetItem(created_date))
                
                # Cases count
                self.annexures_table.setItem(row, 3, QTableWidgetItem(str(annexure['case_count'])))
                
                # Total amount
                amount_item = format_currency_amount(annexure['total_amount'], right_align=True)
                self.annexures_table.setItem(row, 4, amount_item)
                
                # Actions
                actions_widget = self.create_annexure_actions_widget(annexure['id'], annexure['annexure_no'])
                self.annexures_table.setCellWidget(row, 5, actions_widget)
                
                # Store annexure data
                self.annexures_table.item(row, 0).setData(Qt.UserRole, annexure['id'])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load annexures: {str(e)}")

    def create_annexure_actions_widget(self, annexure_id, annexure_no):
        """Create action buttons widget for an annexure"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Approve button
        approve_btn = QPushButton("Approve")
        approve_btn.clicked.connect(lambda: self.approve_annexure(annexure_id, annexure_no))
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: 1px solid #38a169;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #2f855a;
            }
        """)
        layout.addWidget(approve_btn)

        # Decline button
        decline_btn = QPushButton("Decline")
        decline_btn.clicked.connect(lambda: self.decline_annexure(annexure_id, annexure_no))
        decline_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: 1px solid #e53e3e;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        layout.addWidget(decline_btn)

        # View button
        view_btn = QPushButton("View")
        view_btn.clicked.connect(lambda: self.view_annexure_details(annexure_id))
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #3182ce;
                color: white;
                border: 1px solid #3182ce;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #2b6cb0;
            }
        """)
        layout.addWidget(view_btn)

        layout.addStretch()
        return widget

    def approve_annexure(self, annexure_id, annexure_no):
        """Approve an annexure - mark all cases as Written Off"""
        reply = QMessageBox.question(
            self,
            "Approve Annexure",
            f"Are you sure you want to approve annexure {annexure_no}?\n\n"
            "This will mark ALL cases in this annexure as 'Written Off' and they will be finalized.\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Update all cases in the annexure to Written Off status
                cursor.execute("""
                    UPDATE cases
                    SET lc_status = 'Written Off',
                        suffixes = REPLACE(suffixes, '-WOR', '-WO'),
                        is_finalized = 1,
                        finalized_date = ?,
                        finalization_reason = ?
                    WHERE id IN (
                        SELECT case_id FROM annexure_cases WHERE annexure_id = ?
                    )
                """, (
                    datetime.now().strftime("%Y-%m-%d"),
                    "Approved for write-off by CFO/HOD",
                    annexure_id
                ))

                conn.commit()

                # Log the approval
                save_audit_log(
                    "annexure_approved",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "annexure_id": annexure_id,
                        "annexure_no": annexure_no,
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self, "Success",
                    f"Annexure {annexure_no} has been approved.\n\n"
                    "All cases have been marked as 'Written Off' and finalized."
                )

                # Refresh the annexures list
                self.load_annexures()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to approve annexure: {str(e)}")
            finally:
                conn.close()

    def decline_annexure(self, annexure_id, annexure_no):
        """Decline an annexure - return all cases to Write-Off Recommended"""
        reply = QMessageBox.question(
            self,
            "Decline Annexure",
            f"Are you sure you want to decline annexure {annexure_no}?\n\n"
            "This will return ALL cases in this annexure to 'Write-Off Recommended' status.\n\n"
            "The Loss Control Committee will need to reconsider these cases.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Update all cases in the annexure back to Write-Off Recommended
                cursor.execute("""
                    UPDATE cases
                    SET lc_status = 'Write-Off Recommended',
                        is_finalized = 0,
                        finalized_date = NULL,
                        finalization_reason = NULL
                    WHERE id IN (
                        SELECT case_id FROM annexure_cases WHERE annexure_id = ?
                    )
                """, (annexure_id,))

                conn.commit()

                # Log the decline
                save_audit_log(
                    "annexure_declined",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "annexure_id": annexure_id,
                        "annexure_no": annexure_no,
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self, "Success",
                    f"Annexure {annexure_no} has been declined.\n\n"
                    "All cases have been returned to 'Write-Off Recommended' status."
                )

                # Refresh the annexures list
                self.load_annexures()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to decline annexure: {str(e)}")
            finally:
                conn.close()

    def view_annexure_details(self, annexure_id):
        """View detailed information about an annexure"""
        try:
            annexure = get_annexure_details(annexure_id)
            if not annexure:
                QMessageBox.warning(self, "Error", "Annexure not found.")
                return

            # Build details message
            details = f"Annexure: {annexure['annexure_no']}\n"
            details += f"Role: {annexure['role']}\n"
            details += f"Created: {annexure['created_at']}\n"
            details += f"Total Cases: {annexure['case_count']}\n"
            details += f"Total Amount: R {annexure['total_amount']:,.2f}\n\n"

            details += "Cases in Annexure:\n"
            for case in annexure['cases']:
                details += f"  - {case['transaction_no']}: R {case['amount']:,.2f} ({case['responsibility_name']})\n"
                details += f"    Description: {case['description']}\n\n"

            QMessageBox.information(self, "Annexure Details", details)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load annexure details: {str(e)}")

    def export_annexure_excel(self, annexure_id, annexure_no):
        """Export annexure to Excel"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Excel File", f"{annexure_no}.xlsx", 
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                export_annexure_to_excel([annexure_id], file_path)
                QMessageBox.information(self, "Success", f"Excel file saved: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Excel: {str(e)}")

    def export_annexure_pdf(self, annexure_id, annexure_no):
        """Export annexure to PDF"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QInputDialog
            
            # Ask user for PDF options
            include_minutes, ok = QInputDialog.getItem(
                self, "PDF Options", "Include LC Minutes in PDF?",
                ["Annexure Only", "Annexure + LC Minutes"], 0, False
            )
            
            if not ok:
                return
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF File", f"{annexure_no}.pdf", 
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                include_lc_minutes = include_minutes == "Annexure + LC Minutes"
                export_annexure_to_pdf([annexure_id], file_path, include_lc_minutes)
                QMessageBox.information(self, "Success", f"PDF file saved: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def delete_annexure(self, annexure_id, annexure_no):
        """Delete an annexure"""
        reply = QMessageBox.question(
            self,
            "Delete Annexure",
            f"Are you sure you want to delete annexure {annexure_no}?\n\n"
            "This will remove the annexure and return cases to 'Write-Off Recommended' status.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get cases in this annexure
                cursor.execute("SELECT case_id FROM annexure_cases WHERE annexure_id = ?", (annexure_id,))
                case_ids = [row[0] for row in cursor.fetchall()]

                # Update cases back to Write-Off Recommended status
                for case_id in case_ids:
                    cursor.execute("""
                        UPDATE cases 
                        SET write_off_status = NULL
                        WHERE id = ?
                    """, (case_id,))

                # Delete annexure-case relationships
                cursor.execute("DELETE FROM annexure_cases WHERE annexure_id = ?", (annexure_id,))

                # Delete annexure
                cursor.execute("DELETE FROM annexures WHERE id = ?", (annexure_id,))

                conn.commit()

                # Log audit trail
                save_audit_log(
                    "annexure_deleted",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "annexure_id": annexure_id,
                        "annexure_no": annexure_no,
                        "cases_affected": case_ids,
                    },
                    self.fy,
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"Annexure {annexure_no} deleted successfully!\n"
                    f"{len(case_ids)} cases returned to Write-Off Recommended status.",
                )
                self.load_annexures()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete annexure: {str(e)}")
            finally:
                conn.close()

    def refresh_all(self):
        """Refresh both submissions and annexures"""
        self.load_submissions()
        self.load_annexures()
