import datetime
import sqlite3
from collections import defaultdict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QMessageBox, QPushButton,
                             QScrollArea, QSplitter, QTableWidget,
                             QTableWidgetItem, QTextEdit, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.utils import format_currency_amount


class ViewDeletedCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deleted Cases")
        self.setFixedSize(1700, 600)  # Match ViewCasesDialog width
        self.responsibilities = load_responsibilities()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        self.case_table.setColumnCount(6)
        self.case_table.setHorizontalHeaderLabels(
            ["Case No", "Date Reported", "Category", "Amount", "List", "Status"]
        )

        # Enable double-click to view case details (same as ViewCasesDialog)
        self.case_table.itemDoubleClicked.connect(self.show_case_details)

        # Set minimum width for headers and enable proper resizing
        header = self.case_table.horizontalHeader()
        header.setMinimumSectionSize(80)  # Minimum width for each column
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        header.setStretchLastSection(
            True
        )  # Last column stretches to fill remaining space

        # Set default column widths (same as ViewCasesDialog)
        self.case_table.setColumnWidth(0, 120)  # Case No
        self.case_table.setColumnWidth(1, 140)  # Date Reported
        self.case_table.setColumnWidth(2, 150)  # Category
        self.case_table.setColumnWidth(3, 120)  # Amount
        self.case_table.setColumnWidth(4, 120)  # List
        self.case_table.setColumnWidth(5, 120)  # Status

        # Set row height for better readability
        self.case_table.verticalHeader().setDefaultSectionSize(25)

        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

        self.refresh_responsibilities()
        self.refresh_cases()

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}

        # Query database to find responsibilities with deleted cases
        self.responsibilities_with_cases = self.get_responsibilities_with_cases()

        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

    def get_responsibilities_with_cases(self):
        """Get set of responsibility IDs that have deleted cases, including their parents"""
        responsibilities_with_cases = set()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get all responsibility IDs that have deleted cases
            cursor.execute(
                "SELECT DISTINCT responsibility_id FROM cases WHERE list = 'Deleted Cases'"
            )
            case_resp_ids = {row[0] for row in cursor.fetchall()}

            # Include parent responsibilities
            for resp_id in case_resp_ids:
                responsibilities_with_cases.add(resp_id)
                # Find and add parent IDs
                resp = next(
                    (r for r in self.responsibilities if r["id"] == resp_id), None
                )
                if resp and resp["parent_id"]:
                    responsibilities_with_cases.add(resp["parent_id"])

            conn.close()
        except sqlite3.Error as e:
            print(f"Error querying responsibilities with deleted cases: {e}")

        return responsibilities_with_cases

    def add_resp_item(self, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])

        # Bold responsibilities that have deleted cases
        if resp["id"] in self.responsibilities_with_cases:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        if parent_item is None:
            self.resp_tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        children = [r for r in self.responsibilities if r["parent_id"] == resp["id"]]
        for child in children:
            self.add_resp_item(child, item, resp_dict)

    def on_resp_select(self):
        selected = self.resp_tree.selectedItems()
        if selected:
            resp_id = selected[0].data(0, Qt.UserRole)
            subtree_ids = get_subtree_resp_ids(resp_id, self.responsibilities)
            self.refresh_cases(subtree_ids)
        else:
            self.refresh_cases()

    def refresh_cases(self, resp_ids=None):
        self.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            query = f"SELECT transaction_no, date_reported, category, amount, original_list, status FROM cases WHERE list = 'Deleted Cases' AND responsibility_id IN ({placeholders})"
            cursor.execute(query, resp_ids)
        else:
            cursor.execute(
                "SELECT transaction_no, date_reported, category, amount, original_list, status FROM cases WHERE list = 'Deleted Cases'"
            )
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def show_case_details(self, item):
        """Show detailed case information when double-clicking a case"""
        row = item.row()
        case_no = self.case_table.item(row, 0).text()

        # Get full case details from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (case_no,))
        case_data = cursor.fetchone()
        conn.close()

        if case_data:
            dialog = CaseDetailsDialog(case_data, self)
            dialog.exec_()


class CaseDetailsDialog(QDialog):
    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.case_data = case_data
        self.setWindowTitle(
            f"Case Details - {case_data[1]}"
        )  # case_data[1] is transaction_no
        self.setFixedSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create scroll area for case details
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)

        # Case Information Section
        case_info_group = QGroupBox("Case Information")
        case_info_layout = QFormLayout(case_info_group)

        case_info_layout.addRow("Case No:", QLabel(self.case_data[1]))
        case_info_layout.addRow(
            "Date Incurred:", QLabel(self.case_data[2] if self.case_data[2] else "N/A")
        )
        case_info_layout.addRow(
            "Date Identified:",
            QLabel(self.case_data[3] if self.case_data[3] else "N/A"),
        )
        case_info_layout.addRow(
            "Date Reported:", QLabel(self.case_data[4] if self.case_data[4] else "N/A")
        )
        case_info_layout.addRow(
            "Category:", QLabel(self.case_data[9] if self.case_data[9] else "N/A")
        )
        case_info_layout.addRow(
            "Amount:",
            QLabel(
                format_currency_amount(self.case_data[11])
                if self.case_data[11]
                else "N/A"
            ),
        )
        case_info_layout.addRow(
            "List:", QLabel(self.case_data[16] if self.case_data[16] else "N/A")
        )
        case_info_layout.addRow(
            "Status:", QLabel(self.case_data[17] if self.case_data[17] else "N/A")
        )

        scroll_layout.addRow(case_info_group)

        # Description Section
        if self.case_data[5]:  # description
            desc_group = QGroupBox("Description")
            desc_layout = QVBoxLayout(desc_group)
            desc_text = QTextEdit()
            desc_text.setPlainText(self.case_data[5])
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            desc_layout.addWidget(desc_text)
            scroll_layout.addRow(desc_group)

        # Financial Information Section
        financial_group = QGroupBox("Financial Information")
        financial_layout = QFormLayout(financial_group)

        financial_layout.addRow(
            "BAS Payment No:", QLabel(self.case_data[6] if self.case_data[6] else "N/A")
        )
        financial_layout.addRow(
            "BAS Payment Date:",
            QLabel(self.case_data[7] if self.case_data[7] else "N/A"),
        )
        financial_layout.addRow(
            "Persal No:", QLabel(self.case_data[8] if self.case_data[8] else "N/A")
        )

        scroll_layout.addRow(financial_group)

        # Assessment Information Section
        if (
            self.case_data[18] or self.case_data[19]
        ):  # assessment_assessed_by or assessment_date
            assessment_group = QGroupBox("Assessment Information")
            assessment_layout = QFormLayout(assessment_group)

            assessment_layout.addRow(
                "Assessed By:",
                QLabel(self.case_data[18] if self.case_data[18] else "N/A"),
            )
            assessment_layout.addRow(
                "Assessment Date:",
                QLabel(self.case_data[19] if self.case_data[19] else "N/A"),
            )

            scroll_layout.addRow(assessment_group)

        # Additional Information Section
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)

        additional_layout.addRow(
            "Criminal Charges:",
            QLabel(
                self.case_data[22]
                if len(self.case_data) > 22 and self.case_data[22]
                else "N/A"
            ),
        )
        additional_layout.addRow(
            "Disciplinary Process:",
            QLabel(
                self.case_data[23]
                if len(self.case_data) > 23 and self.case_data[23]
                else "N/A"
            ),
        )
        additional_layout.addRow(
            "Loss Recovery:",
            QLabel(
                self.case_data[24]
                if len(self.case_data) > 24 and self.case_data[24]
                else "N/A"
            ),
        )

        scroll_layout.addRow(additional_group)

        # Prevention Steps Section
        if len(self.case_data) > 25 and self.case_data[25]:  # prevention_steps
            prevention_group = QGroupBox("Prevention Steps")
            prevention_layout = QVBoxLayout(prevention_group)
            prevention_text = QTextEdit()
            prevention_text.setPlainText(self.case_data[25])
            prevention_text.setReadOnly(True)
            prevention_text.setMaximumHeight(100)
            prevention_layout.addWidget(prevention_text)
            scroll_layout.addRow(prevention_group)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        permanent_delete_button = QPushButton("Permanent Delete")
        permanent_delete_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; }"
        )
        permanent_delete_button.clicked.connect(self.permanent_delete_case)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(permanent_delete_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def permanent_delete_case(self):
        """Permanently delete the case from the database"""
        case_no = self.case_data[1]  # transaction_no
        amount = self.case_data[11] if self.case_data[11] else 0

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Permanent Delete",
            f"Are you sure you want to permanently delete case '{case_no}'?\n\n"
            f"This action cannot be undone and will completely remove the case from the system.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Set journal mode to WAL
            cursor.execute("PRAGMA journal_mode=WAL;")

            # Delete the case
            cursor.execute("DELETE FROM cases WHERE transaction_no = ?", (case_no,))
            deleted_count = cursor.rowcount

            if deleted_count == 0:
                QMessageBox.warning(
                    self, "Error", f"Case '{case_no}' not found or already deleted."
                )
                conn.close()
                return

            conn.commit()

            # Log audit trail
            fy = get_financial_year()
            save_audit_log(
                "permanent_case_deletion",
                {
                    "case_no": case_no,
                    "amount": amount,
                    "timestamp": datetime.datetime.now().isoformat(),
                },
                fy,
            )

            QMessageBox.information(
                self, "Success", f"Case '{case_no}' has been permanently deleted."
            )

            # Refresh the parent dialog
            if hasattr(self.parent(), "refresh_cases"):
                self.parent().refresh_cases()
            if hasattr(self.parent(), "refresh_responsibilities"):
                self.parent().refresh_responsibilities()

            # Close this dialog
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete case: {e}")
        finally:
            if "conn" in locals():
                conn.close()
