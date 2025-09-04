import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt
from scripts.Utilities.config import DB_PATH


class DuplicateComparisonDialog(QDialog):
    def __init__(self, new_transaction, existing_cases, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Case Comparison")
        self.setFixedSize(1200, 600)

        self.new_transaction = new_transaction
        self.existing_cases = existing_cases
        self.resolution = None  # 'keep' or 'remove'

        self.setup_ui()
        self.populate_comparison()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Compare New Transaction with Existing Cases")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # New transaction section
        new_group = QGroupBox("New Transaction to Import")
        new_layout = QVBoxLayout()

        self.new_details = QTextEdit()
        self.new_details.setMaximumHeight(100)
        self.new_details.setReadOnly(True)
        new_layout.addWidget(self.new_details)

        new_group.setLayout(new_layout)
        layout.addWidget(new_group)

        # Existing cases table
        existing_group = QGroupBox("Potential Duplicate Cases")
        existing_layout = QVBoxLayout()

        self.existing_table = QTableWidget()
        self.existing_table.setColumnCount(8)
        self.existing_table.setHorizontalHeaderLabels([
            "Case No", "Date", "Responsibility", "Category", "Amount", "Status", "List", "Actions"
        ])

        header = self.existing_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.existing_table.setColumnWidth(0, 100)  # Case No
        self.existing_table.setColumnWidth(1, 100)  # Date
        self.existing_table.setColumnWidth(2, 200)  # Responsibility
        self.existing_table.setColumnWidth(3, 150)  # Category
        self.existing_table.setColumnWidth(4, 100)  # Amount
        self.existing_table.setColumnWidth(5, 100)  # Status
        self.existing_table.setColumnWidth(6, 100)  # List
        self.existing_table.setColumnWidth(7, 150)  # Actions

        existing_layout.addWidget(self.existing_table)
        existing_group.setLayout(existing_layout)
        layout.addWidget(existing_group)

        # Decision buttons
        decision_layout = QHBoxLayout()

        self.not_duplicate_button = QPushButton("Not a Duplicate - Keep Both")
        self.not_duplicate_button.clicked.connect(self.mark_not_duplicate)
        self.not_duplicate_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")

        self.is_duplicate_button = QPushButton("Is Duplicate - Remove New Case")
        self.is_duplicate_button.clicked.connect(self.mark_is_duplicate)
        self.is_duplicate_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")

        decision_layout.addWidget(self.not_duplicate_button)
        decision_layout.addWidget(self.is_duplicate_button)
        decision_layout.addStretch()

        layout.addLayout(decision_layout)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

    def populate_comparison(self):
        # Populate new transaction details
        new_details = f"""
Responsibility: {self.new_transaction['responsibility']}
Type: {self.new_transaction['type']}
Amount: R{abs(self.new_transaction['amount']):,.2f}
Date: {self.new_transaction['date'].strftime('%Y-%m-%d')}
Description: {self.new_transaction['description']}
Category: {getattr(self, 'category_name', 'N/A')}
""".strip()

        self.new_details.setPlainText(new_details)

        # Populate existing cases table
        self.existing_table.setRowCount(0)

        for case in self.existing_cases:
            row = self.existing_table.rowCount()
            self.existing_table.insertRow(row)

            # Case No
            self.existing_table.setItem(row, 0, QTableWidgetItem(case.get('transaction_no', '')))

            # Date (use date_reported)
            date_str = case.get('date_reported', '')
            self.existing_table.setItem(row, 1, QTableWidgetItem(date_str))

            # Responsibility (need to look up name)
            resp_name = self.get_responsibility_name(case.get('responsibility_id'))
            self.existing_table.setItem(row, 2, QTableWidgetItem(resp_name))

            # Category
            self.existing_table.setItem(row, 3, QTableWidgetItem(case.get('category', '')))

            # Amount
            amount = case.get('amount', 0)
            amount_str = f"R{amount:,.2f}" if amount else ""
            self.existing_table.setItem(row, 4, QTableWidgetItem(amount_str))

            # Status
            self.existing_table.setItem(row, 5, QTableWidgetItem(case.get('status', '')))

            # List
            self.existing_table.setItem(row, 6, QTableWidgetItem(case.get('list', '')))

            # Actions (View Details button)
            view_button = QPushButton("View Details")
            view_button.clicked.connect(lambda checked, case=case: self.view_case_details(case))
            self.existing_table.setCellWidget(row, 7, view_button)

    def get_responsibility_name(self, resp_id):
        """Get responsibility name from ID"""
        if not resp_id:
            return "N/A"

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM responsibilities WHERE id = ?", (resp_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else f"ID: {resp_id}"
        except sqlite3.Error:
            return f"ID: {resp_id}"

    def view_case_details(self, case):
        """Show detailed view of existing case"""
        details_dialog = CaseDetailsDialog(case, self)
        details_dialog.exec_()

    def mark_not_duplicate(self):
        """Mark that this is not a duplicate - keep both cases"""
        self.resolution = 'keep'
        self.accept()

    def mark_is_duplicate(self):
        """Mark that this is a duplicate - remove the new case"""
        reply = QMessageBox.question(
            self, "Confirm Duplicate",
            "Are you sure this new transaction is a duplicate of an existing case?\n\n"
            "The new transaction will be removed from the import list.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.resolution = 'remove'
            self.accept()

    def get_resolution(self):
        """Return the user's decision"""
        return self.resolution


class CaseDetailsDialog(QDialog):
    """Dialog to show detailed case information"""

    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Case Details - {case_data.get('transaction_no', 'Unknown')}")
        self.setFixedSize(800, 600)

        self.case_data = case_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Case details in a form layout
        form_layout = QFormLayout()

        form_layout.addRow("Case Number:", QLabel(self.case_data.get('transaction_no', 'N/A')))
        form_layout.addRow("Date Incurred:", QLabel(self.case_data.get('date_incurred', 'N/A')))
        form_layout.addRow("Date Identified:", QLabel(self.case_data.get('date_identified', 'N/A')))
        form_layout.addRow("Date Reported:", QLabel(self.case_data.get('date_reported', 'N/A')))
        form_layout.addRow("Category:", QLabel(self.case_data.get('category', 'N/A')))

        # Get responsibility name
        resp_name = self.get_responsibility_name(self.case_data.get('responsibility_id'))
        form_layout.addRow("Responsibility:", QLabel(resp_name))

        amount = self.case_data.get('amount', 0)
        form_layout.addRow("Amount:", QLabel(f"R{amount:,.2f}" if amount else "N/A"))

        form_layout.addRow("Status:", QLabel(self.case_data.get('status', 'N/A')))
        form_layout.addRow("List:", QLabel(self.case_data.get('list', 'N/A')))

        if self.case_data.get('bas_payment_no'):
            form_layout.addRow("BAS Payment No:", QLabel(self.case_data.get('bas_payment_no')))
        if self.case_data.get('bas_payment_date'):
            form_layout.addRow("BAS Payment Date:", QLabel(self.case_data.get('bas_payment_date')))
        if self.case_data.get('bas_journal_no'):
            form_layout.addRow("BAS Journal No:", QLabel(self.case_data.get('bas_journal_no')))
        if self.case_data.get('bas_journal_date'):
            form_layout.addRow("BAS Journal Date:", QLabel(self.case_data.get('bas_journal_date')))

        layout.addLayout(form_layout)

        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        desc_edit = QTextEdit()
        desc_edit.setPlainText(self.case_data.get('description', ''))
        desc_edit.setReadOnly(True)
        desc_edit.setMaximumHeight(100)
        desc_layout.addWidget(desc_edit)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def get_responsibility_name(self, resp_id):
        """Get responsibility name from ID"""
        if not resp_id:
            return "N/A"

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM responsibilities WHERE id = ?", (resp_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else f"ID: {resp_id}"
        except sqlite3.Error:
            return f"ID: {resp_id}"