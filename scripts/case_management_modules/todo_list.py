import sqlite3
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import QDate
from scripts.Utilities.config import DB_PATH


class ToDoListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("To-Do List")
        self.setFixedSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(5)
        self.todo_table.setHorizontalHeaderLabels(["Case No", "Description", "Status", "Action", "Due Date"])
        self.todo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.todo_table)
        self.refresh_todo()

    def refresh_todo(self):
        self.todo_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_no, description, status FROM cases WHERE status IN ('Awaiting Evidence', 'Outstanding BAS Details', 'Missing Supporting Evidence')")
        for row_data in cursor.fetchall():
            row = self.todo_table.rowCount()
            self.todo_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.todo_table.setItem(row, col, QTableWidgetItem(str(data)))
            if row_data[2] == "Outstanding BAS Details":
                action = "BAS Details Required"
            elif row_data[2] == "Missing Supporting Evidence":
                action = "Supporting Evidence Required"
            else:
                action = "Assessment Required"
            self.todo_table.setItem(row, 3, QTableWidgetItem(action))
            due_date = QDate.currentDate().addDays(7).toString("yyyy-MM-dd")
            self.todo_table.setItem(row, 4, QTableWidgetItem(due_date))
        conn.close()