import sqlite3

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QSplitter,
                             QTableWidget, QTableWidgetItem, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout)
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids


class ToDoListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("To-Do List")
        self.setFixedSize(1700, 600)
        self.responsibilities = load_responsibilities()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Main content layout with splitter
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        # Responsibility tree on the left
        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        # Cases table on the right
        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(3)
        self.todo_table.setHorizontalHeaderLabels(["Transaction No", "List", "Status"])

        # Enable selection change to highlight responsibility
        self.todo_table.itemSelectionChanged.connect(self.on_case_select)

        # Set minimum width for headers and enable proper resizing
        header = self.todo_table.horizontalHeader()
        header.setMinimumSectionSize(80)  # Minimum width for each column
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        header.setStretchLastSection(
            True
        )  # Last column stretches to fill remaining space

        # Set default column widths for better layout
        self.todo_table.setColumnWidth(0, 120)  # Transaction No
        self.todo_table.setColumnWidth(1, 120)  # List
        self.todo_table.setColumnWidth(2, 120)  # Status

        # Set row height for better readability
        self.todo_table.verticalHeader().setDefaultSectionSize(25)

        splitter.addWidget(self.todo_table)

        # Set splitter sizes (similar to View Cases)
        splitter.setSizes([300, 1200])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)

        # Load responsibilities and refresh data
        self.refresh_responsibilities()
        self.refresh_todo()

    def refresh_todo(self, resp_ids=None):
        self.todo_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build responsibility filter
        resp_filter = ""
        params = []
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            resp_filter = f"AND responsibility_id IN ({placeholders})"
            params.extend(resp_ids)

        query = f"""
            SELECT transaction_no, 'Checklist' as list, assessment_status as status
            FROM cases
            WHERE list = 'Checklist' AND assessment_status IN ('Alleged', 'Under Assessment') {resp_filter}

            UNION ALL

            SELECT transaction_no, 'Lead Schedule' as list, lc_status as status
            FROM cases
            WHERE list = 'Lead Schedule' AND lc_status = 'Awaiting LC determination' {resp_filter}
        """

        cursor.execute(query, params + params if resp_ids else params)

        for row_data in cursor.fetchall():
            row = self.todo_table.rowCount()
            self.todo_table.insertRow(row)

            # Basic columns
            for col in range(3):
                self.todo_table.setItem(row, col, QTableWidgetItem(str(row_data[col])))

        conn.close()

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

            # Get all responsibility IDs that have cases with todo status
            cursor.execute(
                """
                SELECT DISTINCT responsibility_id FROM cases WHERE list = 'Checklist' AND assessment_status IN ('Alleged', 'Under Assessment')
                UNION ALL
                SELECT DISTINCT responsibility_id FROM cases WHERE list = 'Lead Schedule' AND lc_status = 'Awaiting LC determination'
            """
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
            self.refresh_todo(subtree_ids)
        else:
            self.refresh_todo()

    def on_case_select(self):
        """Highlight the responsibility in the tree when a case is selected"""
        selected_rows = set()
        for item in self.todo_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            # Clear selection if no case is selected
            self.resp_tree.clearSelection()
            return

        # Get the first selected case's responsibility
        first_row = min(selected_rows)
        case_no = self.todo_table.item(first_row, 0).text()

        # Get responsibility_id for this case
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT responsibility_id FROM cases WHERE transaction_no = ?",
                (case_no,),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                responsibility_id = result[0]
                self.highlight_responsibility(responsibility_id)
        except sqlite3.Error as e:
            print(f"Error getting responsibility for case {case_no}: {e}")

    def highlight_responsibility(self, responsibility_id):
        """Find and highlight the responsibility in the tree"""

        def find_item_by_id(parent_item, target_id):
            """Recursively search for an item with the given ID"""
            if parent_item is None:
                # Search top-level items
                for i in range(self.resp_tree.topLevelItemCount()):
                    item = self.resp_tree.topLevelItem(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search children
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            else:
                # Search children of parent_item
                for i in range(parent_item.childCount()):
                    item = parent_item.child(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search grandchildren
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            return None

        # Find the responsibility item
        target_item = find_item_by_id(None, responsibility_id)

        if target_item:
            # Clear current selection
            self.resp_tree.clearSelection()
            # Select the target item
            target_item.setSelected(True)
            # Ensure it's visible
            self.resp_tree.scrollToItem(target_item)
            # Expand parent items to make it visible
            parent = target_item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()

    def _get_supporting_evidence_status(
        self, bas_payment_no, persal_no, category_name, conn
    ):
        """Determine supporting evidence status based on category compulsory settings"""
        if not category_name:
            return "N/A"

        # Query category compulsory settings
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bas_payment_compulsory, persal_compulsory FROM categories WHERE name = ?",
            (category_name,),
        )
        category_data = cursor.fetchone()

        if not category_data:
            return "N/A"

        bas_compulsory, persal_compulsory = category_data

        # Check if required evidence is provided
        bas_provided = bool(bas_payment_no)
        persal_provided = bool(persal_no)

        # Determine status
        if bas_compulsory and not bas_provided:
            return "✗ BAS Required"
        elif persal_compulsory and not persal_provided:
            return "✗ Persal Required"
        elif (bas_compulsory and bas_provided) or (
            persal_compulsory and persal_provided
        ):
            return "✓"
        else:
            return "N/A"
