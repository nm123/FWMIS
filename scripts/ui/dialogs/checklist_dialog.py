import sqlite3

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QMessageBox, QTableWidget,
                             QTableWidgetItem, QVBoxLayout)
from scripts.Utilities.config import DB_PATH


class ChecklistDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Checklist View")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.load_checklist()
        self.setup_table()

    def setup_table(self):
        # Set table headers
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Transaction No", "Category", "Assessment Status"]
        )

        # Make headers stretch to fit
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Connect double-click signal
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_checklist(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT transaction_no, category, assessment_status FROM cases WHERE list = 'Checklist'"
            )
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for row_num, row in enumerate(rows):
                for col_num, data in enumerate(row):
                    self.table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
        except Exception as e:
            QMessageBox.critical(
                self, "Database Error", f"Failed to load checklist: {str(e)}"
            )

    def on_item_double_clicked(self, item):
        row = item.row()
        transaction_no_item = self.table.item(row, 0)
        if transaction_no_item:
            transaction_no = transaction_no_item.text()
            self.edit_case(transaction_no)

    def edit_case(self, transaction_no):
        try:
            # Fetch full case data
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cases WHERE transaction_no = ?", (transaction_no,)
            )
            case_data = cursor.fetchone()
            conn.close()

            if case_data:
                # Import here to avoid circular imports
                from scripts.case_management_modules.edit_case_dialog import \
                    EditCaseDialog

                dialog = EditCaseDialog(case_data, self, "Checklist")
                dialog.exec_()
                # Refresh the table after editing
                self.load_checklist()
            else:
                QMessageBox.warning(
                    self,
                    "Case Not Found",
                    f"Case with transaction number {transaction_no} not found.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open edit dialog: {str(e)}")
