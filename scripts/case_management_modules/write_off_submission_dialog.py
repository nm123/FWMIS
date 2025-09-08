import sqlite3
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QGroupBox,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year


class WriteOffSubmissionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Write-Off Submission")
        self.setFixedSize(900, 700)
        self.fy = get_financial_year()
        self.selected_cases = []
        self.setup_ui()
        self.load_available_cases()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Submission Details Section
        submission_group = QGroupBox("Submission Details")
        submission_layout = QFormLayout(submission_group)

        self.submission_id_edit = QLineEdit()
        self.submission_id_edit.setText(self.generate_submission_id())
        self.submission_id_edit.setReadOnly(True)
        submission_layout.addRow("Submission ID:", self.submission_id_edit)

        self.submission_notes_edit = QTextEdit()
        self.submission_notes_edit.setPlaceholderText("Enter notes for this write-off submission...")
        self.submission_notes_edit.setMaximumHeight(60)
        submission_layout.addRow("Notes:", self.submission_notes_edit)

        layout.addWidget(submission_group)

        # Available Cases Section
        cases_group = QGroupBox("Cases Recommended for Write-Off")
        cases_layout = QVBoxLayout(cases_group)

        # Cases table
        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(5)
        self.cases_table.setHorizontalHeaderLabels([
            "Select", "Case No", "Category", "Amount", "Date Recommended"
        ])

        # Set column widths
        header = self.cases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.cases_table.setColumnWidth(0, 60)   # Select checkbox
        self.cases_table.setColumnWidth(1, 120)  # Case No
        self.cases_table.setColumnWidth(2, 150)  # Category
        self.cases_table.setColumnWidth(3, 100)  # Amount
        self.cases_table.setColumnWidth(4, 140)  # Date Recommended

        cases_layout.addWidget(self.cases_table)

        # Select All checkbox
        select_all_layout = QHBoxLayout()
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        select_all_layout.addWidget(self.select_all_cb)
        select_all_layout.addStretch()
        cases_layout.addLayout(select_all_layout)

        layout.addWidget(cases_group)

        # Summary Section
        summary_group = QGroupBox("Submission Summary")
        summary_layout = QFormLayout(summary_group)

        self.total_cases_label = QLabel("0")
        summary_layout.addRow("Total Cases Selected:", self.total_cases_label)

        self.total_amount_label = QLabel("R 0.00")
        summary_layout.addRow("Total Amount:", self.total_amount_label)

        layout.addWidget(summary_group)

        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create Submission")
        create_btn.clicked.connect(self.create_submission)
        create_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(create_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def generate_submission_id(self):
        """Generate a unique submission ID"""
        fy = self.fy.replace("-", "")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"WO{fy}{timestamp}"

    def load_available_cases(self):
        """Load cases that are recommended for write-off"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, transaction_no, category, determination_amount,
                       determination_date, committee_recommendations
                FROM cases
                WHERE list = 'Write-Off Recommended'
                AND write_off_submission_id IS NULL
                AND is_finalized = 0
                ORDER BY determination_date DESC
            """)

            cases = cursor.fetchall()
            self.cases_table.setRowCount(len(cases))

            for row, case_data in enumerate(cases):
                case_id, transaction_no, category, amount, determination_date, recommendations = case_data

                # Select checkbox
                select_cb = QCheckBox()
                select_cb.stateChanged.connect(self.update_summary)
                self.cases_table.setCellWidget(row, 0, select_cb)

                # Case details
                self.cases_table.setItem(row, 1, QTableWidgetItem(transaction_no))
                self.cases_table.setItem(row, 2, QTableWidgetItem(category or "N/A"))
                amount_item = format_currency_amount(amount, right_align=True)
                self.cases_table.setItem(row, 3, amount_item)
                self.cases_table.setItem(row, 4, QTableWidgetItem(determination_date or "N/A"))

                # Store case data for later use
                self.cases_table.item(row, 1).setData(Qt.UserRole, case_id)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load cases: {str(e)}")
        finally:
            conn.close()

    def toggle_select_all(self, state):
        """Toggle selection of all cases"""
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(state == Qt.Checked)

    def update_summary(self):
        """Update the submission summary based on selected cases"""
        selected_cases = []
        total_amount = 0.0

        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                case_id = self.cases_table.item(row, 1).data(Qt.UserRole)
                amount_text = self.cases_table.item(row, 3).text()

                selected_cases.append(case_id)

                # Extract amount from "R 1,234.56" format
                if amount_text != "N/A":
                    try:
                        amount = float(amount_text.replace("R ", "").replace(",", ""))
                        total_amount += amount
                    except ValueError:
                        pass

        self.selected_cases = selected_cases
        self.total_cases_label.setText(str(len(selected_cases)))
        self.total_amount_label.setText(format_currency_amount(total_amount))

    def create_submission(self):
        """Create the write-off submission"""
        if not self.selected_cases:
            QMessageBox.warning(self, "No Cases Selected", "Please select at least one case for the submission.")
            return

        submission_id = self.submission_id_edit.text().strip()
        notes = self.submission_notes_edit.toPlainText().strip()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create submission record
            cursor.execute("""
                INSERT INTO write_off_submissions (
                    submission_id, fy_id, created_date, status, case_ids,
                    total_amount, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                submission_id,
                None,  # fy_id - could be determined from cases
                datetime.now().strftime("%Y-%m-%d"),
                "Draft",
                json.dumps(self.selected_cases),
                self.get_total_amount(),
                notes
            ))

            # Update cases with submission ID
            for case_id in self.selected_cases:
                cursor.execute("""
                    UPDATE cases
                    SET write_off_submission_id = ?
                    WHERE id = ?
                """, (submission_id, case_id))

            conn.commit()

            # Log audit trail
            save_audit_log("write_off_submission_created", {
                "timestamp": datetime.now().isoformat(),
                "submission_id": submission_id,
                "case_ids": self.selected_cases,
                "total_cases": len(self.selected_cases),
                "total_amount": self.get_total_amount(),
                "notes": notes
            }, self.fy)

            QMessageBox.information(self, "Success",
                                  f"Write-off submission {submission_id} created successfully!\n\n"
                                  f"Cases: {len(self.selected_cases)}\n"
                                  f"Total Amount: {format_currency_amount(self.get_total_amount())}")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create submission: {str(e)}")
        finally:
            conn.close()

    def get_total_amount(self):
        """Calculate total amount from selected cases"""
        total = 0.0
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                amount_text = self.cases_table.item(row, 3).text()
                if amount_text != "N/A":
                    try:
                        amount = float(amount_text.replace("R ", "").replace(",", ""))
                        total += amount
                    except ValueError:
                        pass
        return total