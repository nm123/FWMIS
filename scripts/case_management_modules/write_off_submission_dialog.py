import csv
import os
import sqlite3
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QFileDialog, QGroupBox,
                             QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QTextEdit, QVBoxLayout, QWidget)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.workflow_utils import (approve_write_off_submission,
                                              create_write_off_group)
from scripts.Utilities.write_off_creation_utils import (generate_annexure,
                                                        get_evidence_status)
from scripts.Utilities.write_off_management_utils import (approve_write_off,
                                                          load_group_details)


class WriteOffSubmissionDialog(QDialog):
    """Dialog for creating write-off submissions with case grouping"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Write-Off Submission")
        self.setFixedSize(1000, 800)
        self.fy = get_financial_year()
        self.selected_case_ids = []
        self.setup_ui()
        self.load_write_off_recommended_cases()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select multiple cases from Write-Off Recommended list to create a grouped submission.\n"
            "All selected cases will be assigned the same submission ID and can be approved together."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            "color: #666; font-style: italic; margin-bottom: 10px;"
        )
        layout.addWidget(instructions)

        # Cases Table
        cases_group = QGroupBox("Write-Off Recommended Cases")
        cases_layout = QVBoxLayout(cases_group)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(6)
        self.cases_table.setHorizontalHeaderLabels(
            ["Select", "Case No", "Date Reported", "Category", "Amount", "Evidence"]
        )

        # Set column widths
        header = self.cases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.cases_table.setColumnWidth(0, 60)  # Select
        self.cases_table.setColumnWidth(1, 120)  # Case No
        self.cases_table.setColumnWidth(2, 140)  # Date Reported
        self.cases_table.setColumnWidth(3, 150)  # Category
        self.cases_table.setColumnWidth(4, 120)  # Amount
        self.cases_table.setColumnWidth(5, 200)  # Evidence

        cases_layout.addWidget(self.cases_table)
        layout.addWidget(cases_group)

        # Selection summary
        self.summary_label = QLabel("Selected: 0 cases, Total: R 0.00")
        self.summary_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(self.summary_label)

        # Action buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_cases)
        button_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_selection_btn)

        button_layout.addStretch()

        self.generate_submission_btn = QPushButton("Generate Write-Off Submission")
        self.generate_submission_btn.clicked.connect(self.generate_submission)
        self.generate_submission_btn.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; font-weight: bold; }"
        )
        button_layout.addWidget(self.generate_submission_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_write_off_recommended_cases(self):
        """Load cases that are in Write-Off Recommended status"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Get cases with -WOR suffix (Write-Off Recommended)
            cursor.execute(
                """
                SELECT id, base_transaction_no, date_reported, category, amount, evidence_paths
                FROM cases
                WHERE suffixes LIKE '%-WOR%' AND is_finalized = 0
                ORDER BY base_transaction_no
            """
            )

            cases = cursor.fetchall()
            self.cases_table.setRowCount(len(cases))

            for row, case_data in enumerate(cases):
                (
                    case_id,
                    base_transaction_no,
                    date_reported,
                    category,
                    amount,
                    evidence_paths,
                ) = case_data

                # Checkbox for selection
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(self.update_selection_summary)
                self.cases_table.setCellWidget(row, 0, checkbox)

                # Case No
                self.cases_table.setItem(row, 1, QTableWidgetItem(base_transaction_no))

                # Date Reported
                self.cases_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(str(date_reported) if date_reported else ""),
                )

                # Category
                self.cases_table.setItem(
                    row, 3, QTableWidgetItem(str(category) if category else "")
                )

                # Amount
                amount_item = format_currency_amount(amount, right_align=True)
                self.cases_table.setItem(row, 4, amount_item)

                # Evidence status
                evidence_status = get_evidence_status(evidence_paths)
                self.cases_table.setItem(row, 5, QTableWidgetItem(evidence_status))

                # Store case_id in the row
                self.cases_table.item(row, 1).setData(Qt.UserRole, case_id)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load cases: {str(e)}")
        finally:
            conn.close()

    def select_all_cases(self):
        """Select all cases in the table"""
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def clear_selection(self):
        """Clear all selections"""
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def update_selection_summary(self):
        """Update the selection summary label"""
        selected_cases = []
        total_amount = 0.0

        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                case_id = self.cases_table.item(row, 1).data(Qt.UserRole)
                amount_text = (
                    self.cases_table.item(row, 4)
                    .text()
                    .replace("R ", "")
                    .replace(",", "")
                )
                try:
                    amount = float(amount_text)
                    total_amount += amount
                except ValueError:
                    pass
                selected_cases.append(case_id)

        self.selected_case_ids = selected_cases
        formatted_amount = format_currency_amount(total_amount)
        self.summary_label.setText(
            f"Selected: {len(selected_cases)} cases, Total: {formatted_amount}"
        )

        # Enable/disable generate button
        self.generate_submission_btn.setEnabled(len(selected_cases) > 0)

    def generate_submission(self):
        """Generate a write-off submission for selected cases"""
        if not self.selected_case_ids:
            QMessageBox.warning(
                self, "No Selection", "Please select at least one case."
            )
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Generate Write-Off Submission",
            f"Are you sure you want to create a write-off submission for {len(self.selected_case_ids)} cases?\n\n"
            "This will assign a group ID to all selected cases and allow them to be approved together.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Generate the group ID
            group_id = create_write_off_group(self.selected_case_ids)

            if group_id:
                # Generate annexure (CSV export)
                generate_annexure(group_id, self.fy)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Write-off submission created successfully!\n\n"
                    f"Group ID: {group_id}\n"
                    f"Cases grouped: {len(self.selected_case_ids)}\n\n"
                    f"An annexure has been generated and saved.",
                )

                self.accept()
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to create write-off submission."
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate submission: {str(e)}"
            )


class WriteOffApprovalDialog(QDialog):
    """Dialog for approving write-off submissions"""

    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setWindowTitle(f"Approve Write-Off Submission - {group_id}")
        self.setFixedSize(800, 600)
        self.fy = get_financial_year()
        self.setup_ui()
        self.load_group_details()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Group info
        info_group = QGroupBox("Submission Details")
        info_layout = QVBoxLayout(info_group)

        self.info_label = QLabel()
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_group)

        # Cases table
        cases_group = QGroupBox("Cases in Submission")
        cases_layout = QVBoxLayout(cases_group)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(5)
        self.cases_table.setHorizontalHeaderLabels(
            ["Case No", "Category", "Amount", "Assessment Status", "Evidence"]
        )

        header = self.cases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.cases_table.setColumnWidth(0, 120)  # Case No
        self.cases_table.setColumnWidth(1, 150)  # Category
        self.cases_table.setColumnWidth(2, 120)  # Amount
        self.cases_table.setColumnWidth(3, 140)  # Assessment Status
        self.cases_table.setColumnWidth(4, 200)  # Evidence

        cases_layout.addWidget(self.cases_table)
        layout.addWidget(cases_group)

        # Approval notes
        notes_group = QGroupBox("Approval Notes (Optional)")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter any approval notes...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.approve_btn = QPushButton("Approve Write-Off")
        self.approve_btn.clicked.connect(self.approve_submission)
        self.approve_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; font-weight: bold; }"
        )
        button_layout.addWidget(self.approve_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_group_details(self):
        """Load details of the write-off group"""
        try:
            summary_text, case_list = load_group_details(self.group_id)
            self.info_label.setText(summary_text)
            self.cases_table.setRowCount(len(case_list))
            for row, case in enumerate(case_list):
                self.cases_table.setItem(row, 0, QTableWidgetItem(case["case_no"]))
                self.cases_table.setItem(row, 1, QTableWidgetItem(case["category"]))
                self.cases_table.setItem(row, 2, QTableWidgetItem(case["amount"]))
                self.cases_table.setItem(
                    row, 3, QTableWidgetItem(case["assessment_status"])
                )
                self.cases_table.setItem(row, 4, QTableWidgetItem(case["evidence"]))
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load group details: {str(e)}"
            )

    def approve_submission(self):
        """Approve the write-off submission"""
        notes = self.notes_edit.toPlainText().strip()

        reply = QMessageBox.question(
            self,
            "Approve Write-Off",
            f"Are you sure you want to approve write-off submission {self.group_id}?\n\n"
            "This will finalize all cases in the submission and they will appear in the Written Off list.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                success = approve_write_off(self.group_id, notes)

                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Write-off submission {self.group_id} has been approved!\n\n"
                        "All cases have been finalized and moved to Written Off.",
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self, "Error", "Failed to approve write-off submission."
                    )

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to approve submission: {str(e)}"
                )
