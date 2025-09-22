import json
import sqlite3
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QMessageBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.utils import format_currency_amount


class WriteOffManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Write-Off Submission Management")
        self.setFixedSize(1000, 700)
        self.fy = get_financial_year()
        self.setup_ui()
        self.load_submissions()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Submissions Table
        submissions_group = QGroupBox("Write-Off Submissions")
        submissions_layout = QVBoxLayout(submissions_group)

        self.submissions_table = QTableWidget()
        self.submissions_table.setColumnCount(7)
        self.submissions_table.setHorizontalHeaderLabels(
            [
                "Submission ID",
                "Created Date",
                "Status",
                "Cases",
                "Total Amount",
                "Actions",
                "Details",
            ]
        )

        # Set column widths
        header = self.submissions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.submissions_table.setColumnWidth(0, 150)  # Submission ID
        self.submissions_table.setColumnWidth(1, 120)  # Created Date
        self.submissions_table.setColumnWidth(2, 100)  # Status
        self.submissions_table.setColumnWidth(3, 80)  # Cases
        self.submissions_table.setColumnWidth(4, 120)  # Total Amount
        self.submissions_table.setColumnWidth(5, 200)  # Actions
        self.submissions_table.setColumnWidth(6, 200)  # Details

        submissions_layout.addWidget(self.submissions_table)
        layout.addWidget(submissions_group)

        # Action Buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_submissions)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

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
