import sqlite3
from collections import defaultdict

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QSplitter, QTableWidget, QTableWidgetItem,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                             QWidget)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.case_data_refresh_utils import refresh_cases
from scripts.Utilities.case_filter_utils import (
    get_responsibilities_with_cases, search_case_by_number)
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (get_all_financial_years,
                                               get_current_open_financial_year,
                                               get_financial_year)
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.ui_theme import create_professional_button
from scripts.Utilities.utils import format_currency_amount

from scripts.ui.dialogs.edit_case import EditCaseDialog

from .case_table_utils import (create_table_button, populate_case_table,
                               setup_case_table_columns, create_totals_widget)


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


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
            self.setAttribute(
                Qt.WA_DeleteOnClose, False
            )  # Don't auto-delete to prevent crashes
            self.setAttribute(Qt.WA_QuitOnClose, False)  # Don't quit app on close

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
        self.fy_filter_combo.currentTextChanged.connect(lambda: refresh_cases(self))

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
        self.list_filter_combo.addItems(
            [
                "Checklist",
                "Lead Schedule",
                "Recovery in Progress",
                "Recovered",
                "Write-Off Recommended",
                "Written Off",
            ]
        )
        self.list_filter_combo.setCurrentText("Checklist")
        self.list_filter_combo.setFixedWidth(150)
        self.list_filter_combo.currentTextChanged.connect(
            lambda: (
                print("DEBUG: list_filter_combo triggered refresh_cases"),
                refresh_cases(self),
            )
        )

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
            self.resp_tree.itemSelectionChanged.connect(
                lambda: (
                    print("DEBUG: resp_tree selection changed"),
                    self.on_resp_select(),
                )
            )
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
            setup_case_table_columns(self.case_table, include_edit=True)
            # Set table widget attributes for stability
            self.case_table.setAttribute(Qt.WA_DeleteOnClose, False)
            print("DEBUG: case_table headers set")
        except Exception as e:
            print(f"DEBUG: Error creating case_table: {e}")
            import traceback

            traceback.print_exc()
            return

        # Enable selection change to highlight responsibility
        self.case_table.itemSelectionChanged.connect(
            lambda: (
                print("DEBUG: case_table selection changed"),
                self.on_case_select(),
            )
        )
        print("DEBUG: case_table selection signal connected")

        # Enable double-click to view case details
        self.case_table.itemDoubleClicked.connect(self.show_case_details)
        print("DEBUG: case_table double-click signal connected")

        # Set minimum width for headers and enable proper resizing
        header = self.case_table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # Set row height for better button display and wrapped text
        self.case_table.verticalHeader().setDefaultSectionSize(80)

        # Create a container for the table and totals
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the table
        table_layout.addWidget(self.case_table)
        
        # Add totals widget
        self.totals_widget = create_totals_widget("Checklist")
        table_layout.addWidget(self.totals_widget)
        
        splitter.addWidget(table_container)
        print("DEBUG: table_container with totals added to splitter")

        splitter.setSizes([300, 700])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)
        print("DEBUG: Layout setup completed")

        print("DEBUG: About to call refresh_responsibilities()")
        self.refresh_responsibilities()
        print("DEBUG: refresh_responsibilities() completed")

        print("DEBUG: About to call refresh_cases()")
        refresh_cases(self)
        print("DEBUG: refresh_cases() completed")

        print("DEBUG: EditCasesDialog.setup_ui() completed successfully")

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}

        # Query database to find responsibilities with cases
        self.responsibilities_with_cases = get_responsibilities_with_cases(
            self.fy_filter_combo
        )

        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

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
            refresh_cases(self, subtree_ids)
        else:
            refresh_cases(self)

    def show_case_details(self, item):
        """Show editable case details when double-clicking a case"""
        row = item.row()
        display_case_no = self.case_table.item(row, 0).text()

        # With new schema, transaction_no is base_transaction_no + suffixes
        # display_case_no might be stripped, so we need to find the actual transaction_no
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Try to find case by base_transaction_no (display might be stripped)
        cursor.execute(
            "SELECT * FROM cases WHERE base_transaction_no = ? OR transaction_no = ?",
            (display_case_no, display_case_no),
        )
        case_data = cursor.fetchone()

        # If not found and display_case_no has no suffix, try with common suffixes
        if not case_data and "-" not in display_case_no:
            for suffix in ["-LS", "-WOR", "-REC", "-WO"]:
                cursor.execute(
                    "SELECT * FROM cases WHERE transaction_no = ?",
                    (f"{display_case_no}{suffix}",),
                )
                case_data = cursor.fetchone()
                if case_data:
                    break

        conn.close()

        if case_data:
            selected_list = self.list_filter_combo.currentText()
            print(f"DEBUG: selected_list = '{selected_list}'")
            dialog = EditCaseDialog(case_data, self, selected_list)
            if dialog.exec_():
                # Refresh the table after editing
                refresh_cases(self)

    def search_case_by_number(self):
        """Search for a specific case by case number"""
        case_no = self.case_search_edit.text().strip()
        if not case_no:
            refresh_cases(self)
            return

        rows = search_case_by_number(
            case_no, self.fy_filter_combo, self.list_filter_combo
        )
        populate_case_table(
            self.case_table,
            rows,
            self.list_filter_combo.currentText(),
            include_edit=True,
            edit_callback=self.edit_case_by_row,
        )

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
            cursor.execute(
                "SELECT responsibility_id FROM cases WHERE base_transaction_no = ? OR transaction_no = ?",
                (display_case_no, display_case_no),
            )
            result = cursor.fetchone()
            if result:
                responsibility_id = result[0]
            # If not found and display_case_no has no suffix, try with common suffixes
            elif "-" not in display_case_no:
                for suffix in ["-LS", "-WOR", "-REC", "-WO"]:
                    cursor.execute(
                        "SELECT responsibility_id FROM cases WHERE transaction_no = ?",
                        (f"{display_case_no}{suffix}",),
                    )
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
                    parent_resp = next(
                        (
                            r
                            for r in self.responsibilities
                            if r["id"] == current_parent_id
                        ),
                        None,
                    )
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
            print(
                f"DEBUG: Executing query: SELECT id, base_transaction_no, date_incurred, date_identified, date_reported, description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category, responsibility_id, amount, source_document, supporting_evidence_path, minutes, recovery_evidence_path, evidence_paths, evidence_path, assessment_status, lc_status, criminal_charges, disciplinary_process, loss_recovery, prevention_steps, is_finalized, finalized_date, finalization_reason, write_off_group_id, fy_id, period_id, suffixes FROM cases WHERE base_transaction_no = ? OR transaction_no = ? with params ({display_case_no}, {display_case_no})"
            )
            cursor.execute(
                "SELECT id, base_transaction_no, date_incurred, date_identified, date_reported, description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category, responsibility_id, amount, source_document, supporting_evidence_path, minutes, recovery_evidence_path, evidence_paths, evidence_path, assessment_status, lc_status, criminal_charges, disciplinary_process, loss_recovery, prevention_steps, is_finalized, finalized_date, finalization_reason, write_off_group_id, fy_id, period_id, suffixes FROM cases WHERE base_transaction_no = ? OR transaction_no = ?",
                (display_case_no, display_case_no),
            )
            case_data = cursor.fetchone()
            print(f"DEBUG: Query result: {case_data is not None}")
            if case_data:
                print(f"DEBUG: Found case data with {len(case_data)} columns")
                print(f"DEBUG: First few columns: {case_data[:5]}")

            # If not found and display_case_no has no suffix, try with common suffixes
            if not case_data and "-" not in display_case_no:
                print("DEBUG: Case not found, trying with suffixes")
                for suffix in ["-LS", "-WOR", "-REC", "-WO"]:
                    print(f"DEBUG: Trying suffix {suffix}")
                    cursor.execute(
                        "SELECT id, base_transaction_no, date_incurred, date_identified, date_reported, description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category, responsibility_id, amount, source_document, supporting_evidence_path, minutes, recovery_evidence_path, evidence_paths, evidence_path, assessment_status, lc_status, criminal_charges, disciplinary_process, loss_recovery, prevention_steps, is_finalized, finalized_date, finalization_reason, write_off_group_id, fy_id, period_id, suffixes FROM cases WHERE transaction_no = ?",
                        (f"{display_case_no}{suffix}",),
                    )
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
            selected_list = self.list_filter_combo.currentText()
            print(f"DEBUG: selected_list = '{selected_list}'")
            print("DEBUG: Creating EditCaseDialog")
            try:
                dialog = EditCaseDialog(case_data, self, selected_list)
                print("DEBUG: EditCaseDialog created successfully")
                result = dialog.exec_()
                print(f"DEBUG: EditCaseDialog.exec_() returned {result}")
                if result:
                    print("DEBUG: Refreshing cases after dialog")
                    # Refresh the table after editing
                    refresh_cases(self)
            except Exception as e:
                print(f"DEBUG: Exception creating or executing EditCaseDialog: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(f"DEBUG: No case data found for display_case_no '{display_case_no}'")
            QMessageBox.warning(
                self,
                "Case Not Found",
                f"Could not find case data for case number '{display_case_no}'",
            )
