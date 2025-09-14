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
    QWidget,
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QWheelEvent
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year, get_all_financial_years, get_current_open_financial_year
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.ui_theme import create_professional_button
from collections import defaultdict
from .edit_case_dialog import EditCaseDialog


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


def create_table_button(text):
    """Create a simple, visible button for table cells"""
    button = QPushButton(text)
    button.setFixedSize(50, 20)  # Slightly larger for visibility
    button.setStyleSheet("""
        QPushButton {
            background-color: #007bff;
            color: white;
            border: 1px solid #007bff;
            border-radius: 3px;
            font-size: 11px;
            padding: 2px;
            margin-top: 4px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
    """)
    return button


class EditCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Cases")
        self.setFixedSize(1700, 660)  # Increased height by 10% (60px)
        self.responsibilities = load_responsibilities()
        self.current_list = "Checklist"
        self.refresh_in_progress = False  # Prevent multiple simultaneous refreshes
        self.setup_ui()

    def populate_fy_filter(self):
        """Populate the financial year filter combo box"""
        self.fy_filter_combo.clear()

        # Get all financial years
        financial_years = get_all_financial_years()

        # Add financial years to combo box
        for fy_id, fy_string, is_open in financial_years:
            self.fy_filter_combo.addItem(fy_string, fy_id)

        # Set current open financial year as default
        current_open = get_current_open_financial_year()
        if current_open:
            fy_id, fy_string = current_open
            index = self.fy_filter_combo.findData(fy_id)
            if index >= 0:
                self.fy_filter_combo.setCurrentIndex(index)

    def setup_ui(self):
        print("DEBUG: EditCasesDialog.setup_ui() starting")
        try:
            # Set dialog attributes for better stability
            self.setAttribute(Qt.WA_DeleteOnClose, False)  # Don't auto-delete to prevent crashes
            self.setAttribute(Qt.WA_QuitOnClose, False)    # Don't quit app on close

            layout = QVBoxLayout(self)
            print("DEBUG: Main layout created")
        except Exception as e:
            print(f"DEBUG: Error creating main layout: {e}")
            import traceback
            traceback.print_exc()
            return

        # Compact search bars layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(10)

        # Financial Year filter
        fy_label = QLabel("FY:")
        fy_label.setFixedWidth(20)
        self.fy_filter_combo = NoWheelComboBox()
        self.fy_filter_combo.setFixedWidth(120)
        self.populate_fy_filter()
        self.fy_filter_combo.currentTextChanged.connect(lambda: self.refresh_cases())

        search_layout.addWidget(fy_label)
        search_layout.addWidget(self.fy_filter_combo)

        # Separator
        search_layout.addSpacing(20)

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
        self.list_filter_combo = NoWheelComboBox()
        self.list_filter_combo.addItems(["All Cases", "Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off"])
        self.list_filter_combo.setCurrentText("Checklist")
        self.list_filter_combo.setFixedWidth(150)
        self.list_filter_combo.currentTextChanged.connect(lambda: (print("DEBUG: list_filter_combo triggered refresh_cases"), self.refresh_cases()))

        search_layout.addWidget(list_label)
        search_layout.addWidget(self.list_filter_combo)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Main content layout
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        print("DEBUG: Creating resp_tree")
        try:
            self.resp_tree = QTreeWidget()
            self.resp_tree.setHeaderLabel("Responsibilities")
            self.resp_tree.itemSelectionChanged.connect(lambda: (print("DEBUG: resp_tree selection changed"), self.on_resp_select()))
            # Set tree widget attributes for stability
            self.resp_tree.setAttribute(Qt.WA_DeleteOnClose, False)
            splitter.addWidget(self.resp_tree)
            print("DEBUG: resp_tree created and added to splitter")
        except Exception as e:
            print(f"DEBUG: Error creating resp_tree: {e}")
            import traceback
            traceback.print_exc()
            return

        print("DEBUG: Creating case_table")
        try:
            self.case_table = QTableWidget()
            self.case_table.setColumnCount(8)
            self.case_table.setHorizontalHeaderLabels([
                "Case No", "Date Reported", "Category", "Amount", "List", "Status", "To-Do", "Edit Case"
            ])
            # Set table widget attributes for stability
            self.case_table.setAttribute(Qt.WA_DeleteOnClose, False)
            print("DEBUG: case_table headers set")
        except Exception as e:
            print(f"DEBUG: Error creating case_table: {e}")
            import traceback
            traceback.print_exc()
            return

        # Enable selection change to highlight responsibility
        self.case_table.itemSelectionChanged.connect(lambda: (print("DEBUG: case_table selection changed"), self.on_case_select()))
        print("DEBUG: case_table selection signal connected")

        # Enable double-click to view case details
        self.case_table.itemDoubleClicked.connect(self.show_case_details)
        print("DEBUG: case_table double-click signal connected")

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
        self.case_table.setColumnWidth(7, 90)  # Edit Case

        # Set row height for better button display
        self.case_table.verticalHeader().setDefaultSectionSize(50)

        splitter.addWidget(self.case_table)
        print("DEBUG: case_table added to splitter")

        splitter.setSizes([300, 700])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)
        print("DEBUG: Layout setup completed")

        print("DEBUG: About to call refresh_responsibilities()")
        self.refresh_responsibilities()
        print("DEBUG: refresh_responsibilities() completed")

        print("DEBUG: About to call refresh_cases()")
        self.refresh_cases()
        print("DEBUG: refresh_cases() completed")

        print("DEBUG: EditCasesDialog.setup_ui() completed successfully")

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

            # Build query with financial year filter (but not for "All Cases" list filter)
            query = "SELECT DISTINCT responsibility_id FROM cases WHERE suffixes NOT LIKE '%-DEL%'"
            params = []

            # Add financial year filter if selected
            selected_fy_id = self.fy_filter_combo.currentData()
            if selected_fy_id:
                query += " AND fy_id = ?"
                params.append(selected_fy_id)

            cursor.execute(query, params)
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
        if self.refresh_in_progress:
            print("DEBUG: refresh_cases already in progress, skipping")
            return

        print("DEBUG: Starting refresh_cases in EditCasesDialog")
        self.refresh_in_progress = True
        try:
            self.case_table.setRowCount(0)
            print("DEBUG: Case table cleared")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            print("DEBUG: Database connection established in EditCasesDialog")
        except Exception as e:
            print(f"DEBUG: Error in refresh_cases setup: {e}")
            import traceback
            traceback.print_exc()
            self.refresh_in_progress = False
            return

        # Build base query with list filtering
        base_conditions = []
        params = []

        # Add financial year filter
        selected_fy_id = self.fy_filter_combo.currentData()
        if selected_fy_id:
            base_conditions.append("fy_id = ?")
            params.append(selected_fy_id)

        # Add list filter condition using new single-case model
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "All Cases":
            base_conditions.append("suffixes NOT LIKE '%-DEL%'")
        elif selected_list == "Checklist":
            # Checklist shows all cases (no additional filter)
            pass
        elif selected_list == "Lead Schedule":
            # Lead Schedule shows Confirmed cases with -LS suffix, not finalized
            base_conditions.append("assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO%'")
        elif selected_list == "Write-Off Recommended":
            # Write-Off Recommended shows cases with -WOR suffix
            base_conditions.append("suffixes LIKE '%-WOR%'")
        elif selected_list == "Recovered":
            # Recovered shows cases with -REC suffix
            base_conditions.append("suffixes LIKE '%-REC%'")
        elif selected_list == "Written Off":
            # Written Off shows cases with -WO suffix
            base_conditions.append("suffixes LIKE '%-WO%'")

        # Add responsibility filter if provided
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            base_conditions.append(f"responsibility_id IN ({placeholders})")
            params.extend(resp_ids)

        where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
        query = f"SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"
        print(f"DEBUG: Executing query: {query}")
        print(f"DEBUG: Query params: {params}")

        try:
            cursor.execute(query, params)
            print("DEBUG: Query executed successfully")
            rows = cursor.fetchall()
            print(f"DEBUG: Retrieved {len(rows)} rows from database")

            for i, row_data in enumerate(rows):
                if i % 10 == 0:  # Log progress every 10 rows
                    print(f"DEBUG: Processing row {i}")

                try:
                    row = self.case_table.rowCount()
                    self.case_table.insertRow(row)

                    for col, data in enumerate(row_data):
                        try:
                            if col == 6:  # To-Do column (check both bas_payment_no and bas_journal_no)
                                bas_payment_no = row_data[7] if len(row_data) > 7 else None
                                bas_journal_no = row_data[8] if len(row_data) > 8 else None
                                todo_value = "Yes" if (bas_payment_no or bas_journal_no) else "No"
                                self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                            elif col == 3:  # Amount column
                                amount_item = format_currency_amount(data, right_align=True)
                                self.case_table.setItem(row, col, amount_item)
                            elif col == 0:  # Case No column - transaction_no
                                transaction_no = str(data) if data else ""

                                # For "All Cases" view, show the full transaction_no; for specific list views, strip workflow suffixes
                                if selected_list == "All Cases":
                                    display_value = transaction_no
                                else:
                                    # Strip workflow suffixes for display (-LS, -WOR, -REC, -WO) in specific list views
                                    display_value = transaction_no
                                    for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                                        if display_value.endswith(suffix):
                                            display_value = display_value.rsplit('-', 1)[0]
                                            break

                                self.case_table.setItem(row, col, QTableWidgetItem(display_value))
                            elif col == 4:  # List column - derive from suffixes
                                suffixes = row_data[6] if len(row_data) > 6 else ""
                                if '-WO' in suffixes:
                                    list_value = "Written Off"
                                elif '-REC' in suffixes:
                                    list_value = "Recovered"
                                elif '-WOR' in suffixes:
                                    list_value = "Write-Off Recommended"
                                elif '-LS' in suffixes:
                                    list_value = "Lead Schedule"
                                else:
                                    list_value = "Checklist"
                                self.case_table.setItem(row, col, QTableWidgetItem(list_value))
                            elif col == 5:  # Status column - combine assessment_status and lc_status
                                assessment_status = row_data[4] if len(row_data) > 4 else ""
                                lc_status = row_data[5] if len(row_data) > 5 else ""
                                if lc_status:
                                    status_value = f"{assessment_status}/{lc_status}"
                                else:
                                    status_value = assessment_status
                                self.case_table.setItem(row, col, QTableWidgetItem(status_value))
                            elif col in [1, 2]:  # Date Reported, Category
                                display_value = str(data)
                                self.case_table.setItem(row, col, QTableWidgetItem(display_value))
                        except Exception as cell_error:
                            print(f"DEBUG: Error setting cell ({row}, {col}): {cell_error}")
                            # Continue with other cells

                except Exception as row_error:
                    print(f"DEBUG: Error processing row {i}: {row_error}")
                    # Continue with other rows

                # Add Edit Case button in the last column
                try:
                    edit_button = create_table_button("Edit")
                    edit_button.clicked.connect(lambda checked, r=row: self.edit_case_by_row(r))
                    # Create a container widget for better alignment control
                    container = QWidget()
                    layout = QVBoxLayout(container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.setSpacing(0)
                    layout.addWidget(edit_button, alignment=Qt.AlignCenter)
                    self.case_table.setCellWidget(row, 7, container)
                    print(f"DEBUG: Added edit button to row {row}, column 7")
                except Exception as e:
                    print(f"DEBUG: Error setting up edit button for row {row}: {e}")
                    # Continue without the button rather than crashing
        except Exception as e:
            print(f"DEBUG: Error in database query or row processing: {e}")
            import traceback
            traceback.print_exc()
            self.refresh_in_progress = False
            return

        try:
            conn.close()
            print("DEBUG: Database connection closed in refresh_cases")
        except Exception as e:
            print(f"DEBUG: Error closing database connection: {e}")

        print("DEBUG: refresh_cases completed successfully")
        self.refresh_in_progress = False

    def show_case_details(self, item):
        """Show editable case details when double-clicking a case"""
        row = item.row()
        display_case_no = self.case_table.item(row, 0).text()

        # With new schema, transaction_no is base_transaction_no + suffixes
        # display_case_no might be stripped, so we need to find the actual transaction_no
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Try to find case by base_transaction_no (display might be stripped)
        cursor.execute("SELECT * FROM cases WHERE base_transaction_no = ? OR transaction_no = ?", (display_case_no, display_case_no))
        case_data = cursor.fetchone()

        # If not found and display_case_no has no suffix, try with common suffixes
        if not case_data and '-' not in display_case_no:
            for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (f"{display_case_no}{suffix}",))
                case_data = cursor.fetchone()
                if case_data:
                    break

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

        # Add financial year filter
        selected_fy_id = self.fy_filter_combo.currentData()
        if selected_fy_id:
            base_conditions.append("fy_id = ?")
            params.append(selected_fy_id)

        # Add list filter condition using new single-case model
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "All Cases":
            base_conditions.append("suffixes NOT LIKE '%-DEL%'")
        elif selected_list == "Checklist":
            # Checklist shows all cases (no additional filter)
            pass
        elif selected_list == "Lead Schedule":
            # Lead Schedule shows Confirmed cases with -LS suffix, not finalized
            base_conditions.append("assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO%'")
        elif selected_list == "Write-Off Recommended":
            # Write-Off Recommended shows cases with -WOR suffix
            base_conditions.append("suffixes LIKE '%-WOR%'")
        elif selected_list == "Recovered":
            # Recovered shows cases with -REC suffix
            base_conditions.append("suffixes LIKE '%-REC%'")
        elif selected_list == "Written Off":
            # Written Off shows cases with -WO suffix
            base_conditions.append("suffixes LIKE '%-WO%'")

        where_clause = " AND ".join(base_conditions)
        query = f"SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                if col == 6:  # To-Do column (check both bas_payment_no and bas_journal_no)
                    bas_payment_no = row_data[7] if len(row_data) > 7 else None
                    bas_journal_no = row_data[8] if len(row_data) > 8 else None
                    todo_value = "Yes" if (bas_payment_no or bas_journal_no) else "No"
                    self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                elif col == 3:  # Amount column
                    amount_item = format_currency_amount(data, right_align=True)
                    self.case_table.setItem(row, col, amount_item)
                elif col == 0:  # Case No column - transaction_no
                    transaction_no = str(data) if data else ""

                    # For "All Cases" view, show the full transaction_no; for specific list views, strip workflow suffixes
                    if selected_list == "All Cases":
                        display_value = transaction_no
                    else:
                        # Strip workflow suffixes for display (-LS, -WOR, -REC, -WO) in specific list views
                        display_value = transaction_no
                        for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                            if display_value.endswith(suffix):
                                display_value = display_value.rsplit('-', 1)[0]
                                break

                    self.case_table.setItem(row, col, QTableWidgetItem(display_value))
                elif col == 4:  # List column - derive from suffixes
                    suffixes = row_data[6] if len(row_data) > 6 else ""
                    if '-WO' in suffixes:
                        list_value = "Written Off"
                    elif '-REC' in suffixes:
                        list_value = "Recovered"
                    elif '-WOR' in suffixes:
                        list_value = "Write-Off Recommended"
                    elif '-LS' in suffixes:
                        list_value = "Lead Schedule"
                    else:
                        list_value = "Checklist"
                    self.case_table.setItem(row, col, QTableWidgetItem(list_value))
                elif col == 5:  # Status column - combine assessment_status and lc_status
                    assessment_status = row_data[4] if len(row_data) > 4 else ""
                    lc_status = row_data[5] if len(row_data) > 5 else ""
                    if lc_status:
                        status_value = f"{assessment_status}/{lc_status}"
                    else:
                        status_value = assessment_status
                    self.case_table.setItem(row, col, QTableWidgetItem(status_value))
                elif col in [1, 2]:  # Date Reported, Category
                    display_value = str(data)
                    self.case_table.setItem(row, col, QTableWidgetItem(display_value))

            # Add Edit Case button in the last column
            edit_button = create_table_button("Edit")
            edit_button.clicked.connect(lambda checked, r=row: self.edit_case_by_row(r))
            # Create a container widget for better alignment control
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(edit_button, alignment=Qt.AlignCenter)
            self.case_table.setCellWidget(row, 7, container)

        conn.close()

    def on_case_select(self):
        """Highlight the responsibility in the tree when a case is selected"""
        selected_rows = set()
        for item in self.case_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            # Clear selection if no case is selected
            self.resp_tree.clearSelection()
            return

        # Get the first selected case's responsibility
        first_row = min(selected_rows)
        display_case_no = self.case_table.item(first_row, 0).text()

        # With new schema, find case by base_transaction_no or transaction_no
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            responsibility_id = None
            # Try to find case by base_transaction_no (display might be stripped)
            cursor.execute("SELECT responsibility_id FROM cases WHERE base_transaction_no = ? OR transaction_no = ?", (display_case_no, display_case_no))
            result = cursor.fetchone()
            if result:
                responsibility_id = result[0]
            # If not found and display_case_no has no suffix, try with common suffixes
            elif '-' not in display_case_no:
                for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                    cursor.execute("SELECT responsibility_id FROM cases WHERE transaction_no = ?", (f"{display_case_no}{suffix}",))
                    result = cursor.fetchone()
                    if result:
                        responsibility_id = result[0]
                        break

            conn.close()

            if responsibility_id:
                self.highlight_responsibility(responsibility_id)
        except sqlite3.Error as e:
            print(f"Error getting responsibility for case {display_case_no}: {e}")

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
                # Recursively collect all parent IDs up to the root
                current_parent_id = resp["parent_id"]
                while current_parent_id:
                    parent_ids_to_include.add(current_parent_id)
                    # Find the parent and get its parent_id
                    parent_resp = next((r for r in self.responsibilities if r["id"] == current_parent_id), None)
                    if parent_resp:
                        current_parent_id = parent_resp["parent_id"]
                    else:
                        current_parent_id = None

        # Include all parent responsibilities
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

    def edit_case_by_row(self, row):
        """Edit case by table row"""
        print(f"DEBUG: edit_case_by_row called with row {row}")
        display_case_no = self.case_table.item(row, 0).text()
        print(f"DEBUG: display_case_no = '{display_case_no}'")

        # With new schema, transaction_no is base_transaction_no + suffixes
        # display_case_no might be stripped, so we need to find the actual transaction_no
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            print("DEBUG: Database connection established in edit_case_by_row")

            # Try to find case by base_transaction_no (display might be stripped)
            print(f"DEBUG: Executing query: SELECT * FROM cases WHERE base_transaction_no = ? OR transaction_no = ? with params ({display_case_no}, {display_case_no})")
            cursor.execute("SELECT * FROM cases WHERE base_transaction_no = ? OR transaction_no = ?", (display_case_no, display_case_no))
            case_data = cursor.fetchone()
            print(f"DEBUG: Query result: {case_data is not None}")
            if case_data:
                print(f"DEBUG: Found case data with {len(case_data)} columns")
                print(f"DEBUG: First few columns: {case_data[:5]}")

            # If not found and display_case_no has no suffix, try with common suffixes
            if not case_data and '-' not in display_case_no:
                print("DEBUG: Case not found, trying with suffixes")
                for suffix in ['-LS', '-WOR', '-REC', '-WO']:
                    print(f"DEBUG: Trying suffix {suffix}")
                    cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (f"{display_case_no}{suffix}",))
                    case_data = cursor.fetchone()
                    if case_data:
                        print(f"DEBUG: Found case with suffix {suffix}")
                        break

            conn.close()
            print("DEBUG: Database connection closed")

        except Exception as e:
            print(f"DEBUG: Exception in edit_case_by_row database operations: {e}")
            import traceback
            traceback.print_exc()
            return

        if case_data:
            print("DEBUG: Creating EditCaseDialog")
            try:
                dialog = EditCaseDialog(case_data, self)
                print("DEBUG: EditCaseDialog created successfully")
                result = dialog.exec_()
                print(f"DEBUG: EditCaseDialog.exec_() returned {result}")
                if result:
                    print("DEBUG: Refreshing cases after dialog")
                    # Refresh the table after editing
                    self.refresh_cases()
            except Exception as e:
                print(f"DEBUG: Exception creating or executing EditCaseDialog: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: No case data found for display_case_no '{display_case_no}'")
            QMessageBox.warning(self, "Case Not Found", f"Could not find case data for case number '{display_case_no}'")