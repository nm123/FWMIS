import sqlite3
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.utils import format_currency_amount
from collections import defaultdict
from .edit_case_dialog import EditCaseDialog


class EditCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Cases")
        self.setFixedSize(1700, 600)
        self.responsibilities = load_responsibilities()
        self.current_list = "Checklist"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Compact search bars layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(10)

        # Case number search
        case_label = QLabel("Case No:")
        case_label.setFixedWidth(60)
        self.case_search_edit = QLineEdit()
        self.case_search_edit.setPlaceholderText("Enter case number...")
        self.case_search_edit.setFixedWidth(150)
        self.case_search_edit.returnPressed.connect(self.search_case_by_number)

        search_layout.addWidget(case_label)
        search_layout.addWidget(self.case_search_edit)

        # Separator
        search_layout.addSpacing(20)

        # Responsibility search
        resp_label = QLabel("Responsibility:")
        resp_label.setFixedWidth(80)
        self.resp_search_edit = QLineEdit()
        self.resp_search_edit.setPlaceholderText("Type to search...")
        self.resp_search_edit.setFixedWidth(200)
        self.resp_search_edit.textChanged.connect(self.filter_responsibilities)

        search_layout.addWidget(resp_label)
        search_layout.addWidget(self.resp_search_edit)

        # Separator
        search_layout.addSpacing(20)

        # List filter
        list_label = QLabel("List:")
        list_label.setFixedWidth(30)
        self.list_filter_combo = QComboBox()
        self.list_filter_combo.addItems(["All Cases", "Checklist", "Lead Schedule"])
        self.list_filter_combo.setCurrentText("All Cases")
        self.list_filter_combo.setFixedWidth(120)
        self.list_filter_combo.currentTextChanged.connect(lambda: self.refresh_cases())

        search_layout.addWidget(list_label)
        search_layout.addWidget(self.list_filter_combo)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Main content layout
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        self.case_table.setColumnCount(7)
        self.case_table.setHorizontalHeaderLabels([
            "Case No", "Date Reported", "Category", "Amount", "List", "Status", "To-Do"
        ])

        # Enable double-click to view case details
        self.case_table.itemDoubleClicked.connect(self.show_case_details)

        # Set minimum width for headers and enable proper resizing
        header = self.case_table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # Set default column widths
        self.case_table.setColumnWidth(0, 120)  # Case No
        self.case_table.setColumnWidth(1, 140)  # Date Reported
        self.case_table.setColumnWidth(2, 150)  # Category
        self.case_table.setColumnWidth(3, 120)  # Amount
        self.case_table.setColumnWidth(4, 120)  # List
        self.case_table.setColumnWidth(5, 120)  # Status
        self.case_table.setColumnWidth(6, 80)   # To-Do

        # Set row height for better readability
        self.case_table.verticalHeader().setDefaultSectionSize(25)

        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)

        self.refresh_responsibilities()
        self.refresh_cases()

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}

        # Query database to find responsibilities with cases
        self.responsibilities_with_cases = self.get_responsibilities_with_cases()

        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

    def get_responsibilities_with_cases(self):
        """Get set of responsibility IDs that have cases, including their parents"""
        responsibilities_with_cases = set()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get all responsibility IDs that have cases
            cursor.execute("SELECT DISTINCT responsibility_id FROM cases WHERE list != 'Deleted Cases'")
            case_resp_ids = {row[0] for row in cursor.fetchall()}

            # Include parent responsibilities
            for resp_id in case_resp_ids:
                responsibilities_with_cases.add(resp_id)
                # Find and add parent IDs
                resp = next((r for r in self.responsibilities if r["id"] == resp_id), None)
                if resp and resp["parent_id"]:
                    responsibilities_with_cases.add(resp["parent_id"])

            conn.close()
        except sqlite3.Error as e:
            print(f"Error querying responsibilities with cases: {e}")

        return responsibilities_with_cases

    def add_resp_item(self, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])

        # Bold responsibilities that have cases
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

        # Build base query with list filtering
        base_conditions = ["list != 'Deleted Cases'"]
        params = []

        # Add list filter condition
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "Checklist":
            base_conditions.append("list = 'Checklist'")
        elif selected_list == "Lead Schedule":
            base_conditions.append("list = 'Lead Schedule'")

        # Add responsibility filter if provided
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            base_conditions.append(f"responsibility_id IN ({placeholders})")
            params.extend(resp_ids)

        where_clause = " AND ".join(base_conditions)
        query = f"SELECT transaction_no, date_reported, category, amount, list, status, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                if col == 6:  # To-Do column (check both bas_payment_no and bas_journal_no)
                    bas_payment_no = row_data[6] if len(row_data) > 6 else None
                    bas_journal_no = row_data[7] if len(row_data) > 7 else None
                    todo_value = "Yes" if (bas_payment_no or bas_journal_no) else "No"
                    self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                elif col == 3:  # Amount column
                    amount_item = format_currency_amount(data, right_align=True)
                    self.case_table.setItem(row, col, amount_item)
                elif col < 6:  # Regular columns (skip the extra bas_payment_no column)
                    self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def show_case_details(self, item):
        """Show editable case details when double-clicking a case"""
        row = item.row()
        case_no = self.case_table.item(row, 0).text()

        # Get full case details from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (case_no,))
        case_data = cursor.fetchone()
        conn.close()

        if case_data:
            dialog = EditCaseDialog(case_data, self)
            if dialog.exec_():
                # Refresh the table after editing
                self.refresh_cases()

    def search_case_by_number(self):
        """Search for a specific case by case number"""
        case_no = self.case_search_edit.text().strip()
        if not case_no:
            self.refresh_cases()
            return

        self.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build search query with list filtering
        base_conditions = ["transaction_no LIKE ?"]
        params = [f"%{case_no}%"]

        # Add list filter condition
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "Checklist":
            base_conditions.append("list = 'Checklist'")
        elif selected_list == "Lead Schedule":
            base_conditions.append("list = 'Lead Schedule'")
        else:
            base_conditions.append("list != 'Deleted Cases'")

        where_clause = " AND ".join(base_conditions)
        query = f"SELECT transaction_no, date_reported, category, amount, list, status, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                if col == 6:  # To-Do column (check both bas_payment_no and bas_journal_no)
                    bas_payment_no = row_data[6] if len(row_data) > 6 else None
                    bas_journal_no = row_data[7] if len(row_data) > 7 else None
                    todo_value = "Yes" if (bas_payment_no or bas_journal_no) else "No"
                    self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                elif col == 3:  # Amount column
                    amount_item = format_currency_amount(data, right_align=True)
                    self.case_table.setItem(row, col, amount_item)
                elif col < 6:  # Regular columns (skip the extra bas_payment_no column)
                    self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def filter_responsibilities(self, text):
        """Filter responsibilities based on search text"""
        text = text.lower()
        if not text:
            self.refresh_responsibilities()
            return

        self.resp_tree.clear()

        # Find responsibilities that match the search text
        matching_resps = []
        parent_ids_to_include = set()

        for resp in self.responsibilities:
            if text in resp["name"].lower():
                matching_resps.append(resp)
                # Also include the parent if it exists
                if resp["parent_id"]:
                    parent_ids_to_include.add(resp["parent_id"])

        # Include parent responsibilities
        for resp in self.responsibilities:
            if resp["id"] in parent_ids_to_include:
                matching_resps.append(resp)

        # Remove duplicates while preserving order
        seen_ids = set()
        filtered_resps = []
        for resp in matching_resps:
            if resp["id"] not in seen_ids:
                filtered_resps.append(resp)
                seen_ids.add(resp["id"])

        # Create parent map for filtered results
        parent_map = defaultdict(list)
        for resp in filtered_resps:
            parent_map[resp["parent_id"]].append(resp)

        def add_filtered_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])

                # Bold responsibilities that have cases
                if resp["id"] in self.responsibilities_with_cases:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)

                if parent_id is None:
                    self.resp_tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        self.resp_tree.expandAll()