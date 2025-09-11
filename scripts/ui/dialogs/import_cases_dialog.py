import os
import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QDateEdit, QFileDialog, QMessageBox, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QProgressBar, QGroupBox, QTextEdit, QComboBox, QCheckBox, QGridLayout
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

try:
    # Try relative imports first (when used as part of a package)
    from ...models.bas_parser import BASParser
    from ...core.import_worker import ImportWorker
    from .transaction_details_dialog import TransactionDetailsDialog
except ImportError:
    # Fall back to absolute imports (when run directly)
    from scripts.models.bas_parser import BASParser
    from scripts.core.import_worker import ImportWorker
    from scripts.ui.dialogs.transaction_details_dialog import TransactionDetailsDialog
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.responsibility_utils import load_posting_responsibilities
from scripts.Utilities.category_utils import load_categories
from scripts.category_management import ManageCategoriesDialog
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.responsibility_management_actions import edit_responsibility_by_name
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.ui_theme import apply_theme, create_professional_button, create_professional_groupbox, setup_professional_table, create_status_label


class ImportUndisclosedCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 FWMIS - Import Undisclosed Cases from BAS Report")
        self.setFixedSize(1450, 900)
        self.setWindowIconText("📊")

        # Apply professional theme
        apply_theme(self)

        self.parser = BASParser()
        self.transactions = []
        self.category = None
        self.date_from = None
        self.date_to = None
        self.bas_file_path = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        header_layout = QHBoxLayout()
        header_label = QLabel("📊 Import Undisclosed Cases")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #343a40;
                margin-bottom: 5px;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # File selection section
        file_group = create_professional_groupbox("📁 BAS Report File Selection", "blue")
        file_layout = QHBoxLayout()
        file_layout.setSpacing(10)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Click Browse to select BAS report file (.txt)...")
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setMinimumHeight(35)

        self.browse_button = create_professional_button("📂 Browse", "success")
        self.browse_button.clicked.connect(self.browse_file)

        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Import settings section
        settings_group = create_professional_groupbox("⚙️ Import Configuration")
        settings_layout = QGridLayout()
        settings_layout.setSpacing(15)

        # Category selection
        category_label = QLabel("📋 Category:")
        category_label.setStyleSheet("font-weight: bold;")
        self.category_button = create_professional_button("🎯 Select Category")
        self.category_button.clicked.connect(self.select_category)
        self.category_button.setMinimumHeight(35)
        self.category_label = QLabel("No category selected")
        self.category_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                color: #856404;
                font-style: italic;
            }
        """)

        # Date range selection
        date_label = QLabel("📅 Date Range:")
        date_label.setStyleSheet("font-weight: bold;")

        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(10)

        from_label = QLabel("From:")
        from_label.setMinimumWidth(40)
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setMinimumHeight(35)

        to_label = QLabel("To:")
        to_label.setMinimumWidth(25)
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setMinimumHeight(35)

        date_range_layout.addWidget(from_label)
        date_range_layout.addWidget(self.date_from_edit)
        date_range_layout.addWidget(to_label)
        date_range_layout.addWidget(self.date_to_edit)
        date_range_layout.addStretch()

        # Parse button
        self.parse_button = create_professional_button("🔍 Parse File", "info")
        self.parse_button.clicked.connect(self.parse_file)
        self.parse_button.setEnabled(False)
        self.parse_button.setMinimumHeight(40)

        # Layout arrangement
        settings_layout.addWidget(category_label, 0, 0)
        settings_layout.addWidget(self.category_button, 0, 1)
        settings_layout.addWidget(self.category_label, 0, 2, 1, 2)

        settings_layout.addWidget(date_label, 1, 0)
        settings_layout.addLayout(date_range_layout, 1, 1, 1, 3)

        settings_layout.addWidget(self.parse_button, 2, 1, 1, 2, Qt.AlignCenter)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Results section
        results_group = create_professional_groupbox("📋 Transaction Analysis & Processing", "purple")
        results_layout = QVBoxLayout()
        results_layout.setSpacing(10)

        # Status display
        status_layout = QHBoxLayout()
        self.results_label = create_status_label("⏳ Ready to parse BAS file...", "info")
        self.results_label.setMinimumHeight(40)
        status_layout.addWidget(self.results_label)
        results_layout.addLayout(status_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        results_layout.addWidget(self.progress_bar)

        # Transactions table
        table_container = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_header = QLabel("📊 Parsed Transactions:")
        table_header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 5px;
            }
        """)
        table_layout.addWidget(table_header)

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(9)
        self.transactions_table.setHorizontalHeaderLabels([
            "🏢 Responsibility", "🔢 Type", "💰 Amount", "📅 Date", "📝 Description",
            "✅ Resp Status", "🔍 Dup Status", "🎫 Case Number", "⚡ Actions"
        ])

        setup_professional_table(self.transactions_table)

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.transactions_table.setColumnWidth(0, 200)  # Responsibility
        self.transactions_table.setColumnWidth(1, 70)   # Type
        self.transactions_table.setColumnWidth(2, 110)  # Amount
        self.transactions_table.setColumnWidth(3, 110)  # Date
        self.transactions_table.setColumnWidth(4, 220)  # Description
        self.transactions_table.setColumnWidth(5, 110)  # Resp Status
        self.transactions_table.setColumnWidth(6, 110)  # Dup Status
        self.transactions_table.setColumnWidth(7, 130)  # Case Number

        # Connect double-click signal for editing responsibilities
        self.transactions_table.itemDoubleClicked.connect(self.on_table_double_click)

        # Set minimum row height to accommodate buttons
        self.transactions_table.verticalHeader().setDefaultSectionSize(60)

        table_layout.addWidget(self.transactions_table)
        table_container.setLayout(table_layout)
        results_layout.addWidget(table_container)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Action buttons section
        actions_group = create_professional_groupbox("🎯 Import Actions", "red")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(15)

        # Workflow buttons
        workflow_layout = QHBoxLayout()
        workflow_layout.setSpacing(12)

        self.manage_resp_button = create_professional_button("👥 Manage Responsibilities", "purple")
        self.manage_resp_button.clicked.connect(self.manage_responsibilities)
        self.manage_resp_button.setEnabled(False)
        self.manage_resp_button.setMinimumHeight(40)

        self.check_duplicates_button = create_professional_button("🔍 Check Duplicates", "warning")
        self.check_duplicates_button.clicked.connect(self.check_duplicates)
        self.check_duplicates_button.setEnabled(False)
        self.check_duplicates_button.setMinimumHeight(40)

        self.assign_case_numbers_button = create_professional_button("🎫 Assign Case Numbers", "info")
        self.assign_case_numbers_button.clicked.connect(self.assign_case_numbers)
        self.assign_case_numbers_button.setEnabled(False)
        self.assign_case_numbers_button.setMinimumHeight(45)

        workflow_layout.addWidget(self.manage_resp_button)
        workflow_layout.addWidget(self.check_duplicates_button)
        workflow_layout.addWidget(self.assign_case_numbers_button)
        workflow_layout.addStretch()

        actions_layout.addLayout(workflow_layout)

        # Final action buttons
        final_actions_layout = QHBoxLayout()
        final_actions_layout.addStretch()

        self.import_button = create_professional_button("🚀 Import Cases", "success")
        self.import_button.clicked.connect(self.import_cases)
        self.import_button.setEnabled(False)
        self.import_button.setMinimumHeight(50)

        self.cancel_button = create_professional_button("❌ Cancel", "secondary")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(45)

        final_actions_layout.addWidget(self.import_button)
        final_actions_layout.addWidget(self.cancel_button)

        actions_layout.addLayout(final_actions_layout)
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select BAS Report File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.bas_file_path = file_path
            self.parse_button.setEnabled(bool(self.category))

    def select_category(self):
        dialog = ManageCategoriesDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_category()
            if selected:
                self.category = selected
                self.category_label.setText(f"✅ {selected['name']}")
                self.category_label.setStyleSheet("""
                    QLabel {
                        background-color: #d4edda;
                        border: 2px solid #28a745;
                        border-radius: 6px;
                        padding: 8px;
                        color: #155724;
                        font-weight: bold;
                        font-size: 13px;
                    }
                """)
                self.parse_button.setEnabled(bool(self.bas_file_path))

    def parse_file(self):
        if not self.bas_file_path or not self.category:
            return

        try:
            # First parse to extract dates from header
            temp_transactions = self.parser.parse_file(self.bas_file_path, None, None)
            extracted_dates = self.parser.get_extracted_dates()

            # If dates were extracted from header, use them
            if extracted_dates['date_from'] and extracted_dates['date_to']:
                self.date_from_edit.setDate(QDate(extracted_dates['date_from']))
                self.date_to_edit.setDate(QDate(extracted_dates['date_to']))
                QMessageBox.information(
                    self, "Dates Extracted",
                    f"Dates automatically extracted from report header:\n"
                    f"From: {extracted_dates['date_from'].strftime('%d/%m/%Y')}\n"
                    f"To: {extracted_dates['date_to'].strftime('%d/%m/%Y')}\n\n"
                    f"You can modify these dates if needed."
                )

            self.date_from = self.date_from_edit.date().toPyDate()
            self.date_to = self.date_to_edit.date().toPyDate()

            # Re-parse with the correct date range
            self.transactions = self.parser.parse_file(self.bas_file_path, self.date_from, self.date_to)

            self.results_label.setText(self.parser.get_transaction_summary())
            self.populate_transactions_table()

            # Enable next steps
            self.manage_resp_button.setEnabled(True)
            self.check_duplicates_button.setEnabled(True)
            # Note: Import button will be enabled after duplicate check or case number assignment

        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse BAS file:\n{str(e)}")

    def populate_transactions_table(self):
        # Save current scroll position
        vertical_scroll_pos = self.transactions_table.verticalScrollBar().value()
        horizontal_scroll_pos = self.transactions_table.horizontalScrollBar().value()

        self.transactions_table.setRowCount(0)

        for i, transaction in enumerate(self.transactions):
            row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row)

            # Check if transaction is marked for removal
            is_marked_for_removal = transaction.get('marked_for_removal', False)

            # Responsibility - make it visually distinct as clickable
            resp_item = QTableWidgetItem(transaction['responsibility'])
            resp_item.setToolTip("Double-click to edit this responsibility")
            resp_item.setForeground(Qt.blue)  # Make it blue to indicate it's clickable
            font = resp_item.font()
            font.setUnderline(True)  # Underline to show it's a link
            resp_item.setFont(font)

            # Apply removal styling if marked for removal
            if is_marked_for_removal:
                resp_item.setBackground(Qt.red)
                resp_item.setForeground(Qt.white)
                resp_item.setToolTip("This transaction is marked for removal")

            self.transactions_table.setItem(row, 0, resp_item)

            # Type
            self.transactions_table.setItem(row, 1, QTableWidgetItem(transaction['type']))

            # Amount - right aligned with comma formatting
            amount_str = f"R{abs(transaction['amount']):,.2f}"
            if transaction['is_credit']:
                amount_str = f"({amount_str})"  # Show credits in parentheses
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.transactions_table.setItem(row, 2, amount_item)

            # Date
            self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction['date'].strftime('%Y-%m-%d')))

            # Description
            self.transactions_table.setItem(row, 4, QTableWidgetItem(transaction['description']))

            # Responsibility Status
            resp_status = self.validate_responsibility(transaction['responsibility'])
            status_item = QTableWidgetItem(resp_status['status'])
            if resp_status['status'] == "Not Found":
                status_item.setBackground(Qt.red)
            elif resp_status['status'] == "Non-Posting":
                status_item.setBackground(Qt.yellow)
            else:
                status_item.setBackground(Qt.green)
            self.transactions_table.setItem(row, 5, status_item)

            # Duplicate Status
            dup_status = "Not Checked"
            has_duplicates = False
            if hasattr(self, 'duplicate_check_results') and i < len(self.duplicate_check_results):
                result = self.duplicate_check_results[i]
                if result['duplicates']:
                    dup_status = f"Duplicates: {len(result['duplicates'])}"
                    has_duplicates = True
                else:
                    dup_status = "No Duplicates"

            # Override status if marked for removal
            if is_marked_for_removal:
                dup_status = "Marked for Removal"

            dup_item = QTableWidgetItem(dup_status)
            if has_duplicates:
                dup_item.setBackground(Qt.yellow)  # Highlight duplicates in yellow
                dup_item.setForeground(Qt.black)
            elif is_marked_for_removal:
                dup_item.setBackground(Qt.red)
                dup_item.setForeground(Qt.white)
            self.transactions_table.setItem(row, 6, dup_item)

            # Also highlight the entire row if it has duplicates
            if has_duplicates:
                for col in range(self.transactions_table.columnCount()):
                    item = self.transactions_table.item(row, col)
                    if item:
                        item.setBackground(Qt.yellow)
                        item.setForeground(Qt.black)

            # Apply removal styling to entire row if marked for removal
            if is_marked_for_removal:
                for col in range(self.transactions_table.columnCount()):
                    item = self.transactions_table.item(row, col)
                    if item:
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)

            # Case Number
            case_number = "Not Assigned"
            if 'case_number' in transaction and transaction['case_number']:
                case_number = transaction['case_number']
            self.transactions_table.setItem(row, 7, QTableWidgetItem(case_number))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            # View Details button
            view_btn = QPushButton("Details")
            view_btn.setMinimumHeight(35)
            view_btn.setMinimumWidth(70)
            view_btn.clicked.connect(lambda checked, trans=transaction: self.view_transaction_details(trans))
            actions_layout.addWidget(view_btn)

            # Compare Duplicates button (only if duplicates exist)
            if has_duplicates:
                compare_btn = QPushButton("Compare")
                compare_btn.setMinimumHeight(35)
                compare_btn.setMinimumWidth(70)
                compare_btn.clicked.connect(lambda checked, trans=transaction, dups=result['duplicates']: self.compare_duplicates(trans, dups))
                compare_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
                actions_layout.addWidget(compare_btn)

            self.transactions_table.setCellWidget(row, 8, actions_widget)

        # Restore scroll position
        self.transactions_table.verticalScrollBar().setValue(vertical_scroll_pos)
        self.transactions_table.horizontalScrollBar().setValue(horizontal_scroll_pos)

    def validate_responsibility(self, responsibility_name):
        """Validate if responsibility exists and is posting level"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_posting_level FROM responsibilities WHERE name = ?", (responsibility_name,))
            result = cursor.fetchone()
            conn.close()

            if result:
                resp_id, is_posting = result
                if is_posting:
                    return {'status': 'Valid', 'id': resp_id}
                else:
                    return {'status': 'Non-Posting', 'id': resp_id}
            else:
                return {'status': 'Not Found', 'id': None}

        except sqlite3.Error as e:
            print(f"Error validating responsibility: {e}")
            return {'status': 'Error', 'id': None}

    def on_table_double_click(self, item):
        """Handle double-click on table items"""
        row = item.row()
        column = item.column()

        # Check if double-click was on the Responsibility column (column 0)
        if column == 0:
            responsibility_name = item.text().strip()
            if responsibility_name and responsibility_name != "Responsibility":
                # Open the edit responsibility dialog for this responsibility
                edit_responsibility_by_name(self, responsibility_name)

    def view_transaction_details(self, transaction):
        """Show detailed view of transaction"""
        details_dialog = TransactionDetailsDialog(transaction, self)
        details_dialog.exec_()

    def compare_duplicates(self, transaction, duplicates):
        """Open duplicate comparison dialog"""
        # Create a copy of the transaction with category name for display
        transaction_copy = transaction.copy()
        transaction_copy['category_name'] = self.category['name'] if self.category else 'N/A'

        # Import the duplicate comparison dialog
        from scripts.case_management_modules.duplicate_comparison_dialog import DuplicateComparisonDialog
        dialog = DuplicateComparisonDialog(transaction_copy, duplicates, self)
        if dialog.exec_():
            resolution = dialog.get_resolution()
            if resolution == 'remove':
                # Mark transaction for removal
                transaction['marked_for_removal'] = True
                # Update table display
                self.populate_transactions_table()
                QMessageBox.information(
                    self, "Transaction Removed",
                    "The transaction has been marked for removal from the import list."
                )

    def manage_responsibilities(self):
        dialog = ResponsibilityManagementDialog(self)
        dialog.exec_()
        # Refresh validation status after potential changes

    def check_duplicates(self):
        """Check for duplicate cases based on responsibility matching"""
        if not self.transactions:
            QMessageBox.warning(self, "No Transactions", "No transactions to check for duplicates")
            return

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_label.setText("Checking for duplicates...")

        total_transactions = len(self.transactions)
        duplicate_count = 0
        no_duplicate_count = 0

        # Initialize duplicate check results
        self.duplicate_check_results = []

        for i, transaction in enumerate(self.transactions):
            self.progress_bar.setValue(int((i / total_transactions) * 100))
            self.results_label.setText(f"Checking transaction {i+1} of {total_transactions}...")

            # Find duplicates for this transaction
            duplicates = self.find_duplicates(transaction)

            # Store result for table display
            result = {
                'transaction_index': i,
                'duplicates': duplicates,
                'duplicate_count': len(duplicates)
            }
            self.duplicate_check_results.append(result)

            if duplicates:
                duplicate_count += 1
            else:
                no_duplicate_count += 1

        self.progress_bar.setVisible(False)

        # Update table to refresh Dup Status column
        self.populate_transactions_table()

        # Show summary
        self.results_label.setText(f"Duplicate check complete: {duplicate_count} with duplicates, {no_duplicate_count} without duplicates")

        QMessageBox.information(
            self, "Duplicate Check Complete",
            f"✅ Duplicate check completed.\n\n"
            f"Transactions with potential duplicates: {duplicate_count}\n"
            f"Transactions without duplicates: {no_duplicate_count}\n\n"
            f"Check the 'Dup Status' column for details.\n"
            f"Rows with duplicates are highlighted in the table."
        )

        # Enable next steps
        self.assign_case_numbers_button.setEnabled(True)
        self.import_button.setEnabled(False)  # Will be enabled after case numbers are assigned

    def find_duplicates(self, transaction):
        """Find potential duplicate cases for a transaction"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year for the transaction date
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Get fy_id for the current financial year
            cursor.execute("SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?", (start_year, end_year))
            fy_result = cursor.fetchone()
            fy_id = fy_result[0] if fy_result else None

            # If fy_id is None, try to get the current open financial year
            if fy_id is None:
                from scripts.Utilities.financial_utils import get_current_open_financial_year
                current_fy = get_current_open_financial_year()
                if current_fy:
                    fy_id = current_fy[0]
                    print(f"DEBUG: Switched to current open FY ID: {fy_id}")
                else:
                    print(f"DEBUG: No open financial year found for duplicate checking")

            print(f"DEBUG: Duplicate checking - Current FY: {fy}, start_year: {start_year}, end_year: {end_year}, fy_id: {fy_id}")

            # Check what FY 149 actually represents
            cursor.execute("""
                SELECT start_year, end_year FROM financial_years WHERE id = 149
            """)
            fy_149_info = cursor.fetchone()
            print(f"DEBUG: FY 149 represents: {fy_149_info}")

            # If FY 149 doesn't exist, this is the root cause!
            if fy_149_info is None:
                print(f"DEBUG: *** DATABASE INTEGRITY ISSUE DETECTED ***")
                print(f"DEBUG: Cases exist with fy_id=149 but no financial year record exists!")
                print(f"DEBUG: This explains why duplicate checking can't find the cases.")
                print(f"DEBUG: The cases are 'orphaned' in a non-existent financial year.")

                # Check what the orphaned cases look like
                cursor.execute("""
                    SELECT transaction_no, responsibility_id, category, amount, list
                    FROM cases WHERE fy_id = 149 AND list != 'Deleted Cases' LIMIT 3
                """)
                orphaned_cases = cursor.fetchall()
                print(f"DEBUG: Sample orphaned cases: {orphaned_cases}")

            # Also check what FY the existing cases are actually in
            cursor.execute("""
                SELECT DISTINCT fy_id, COUNT(*) FROM cases
                WHERE list != 'Deleted Cases'
                GROUP BY fy_id
                ORDER BY fy_id
            """)
            all_fy_cases = cursor.fetchall()
            print(f"DEBUG: All cases by FY ID: {all_fy_cases}")

            # Show details of all FYs with cases
            for fy_id_check, count in all_fy_cases:
                cursor.execute("""
                    SELECT start_year, end_year FROM financial_years WHERE id = ?
                """, (fy_id_check,))
                fy_details = cursor.fetchone()
                print(f"DEBUG: FY ID {fy_id_check}: {fy_details} has {count} cases")

            # Check for orphaned cases in non-existent financial years
            orphaned_fy_ids = []
            for fy_id_check, count in all_fy_cases:
                cursor.execute("""
                    SELECT start_year, end_year FROM financial_years WHERE id = ?
                """, (fy_id_check,))
                fy_details = cursor.fetchone()
                if fy_details is None and count > 0:
                    orphaned_fy_ids.append(fy_id_check)
                    print(f"DEBUG: Found orphaned FY ID {fy_id_check} with {count} cases")

            # If no cases in current FY, try to find cases in other FYs that match the transaction dates
            if fy_id and not any(row[0] == fy_id for row in all_fy_cases):
                print(f"DEBUG: No cases found in current FY {fy} (ID: {fy_id}), checking other FYs...")
                # Look for cases that might match the transaction date range
                for trans in self.transactions[:3]:  # Check first 3 transactions
                    trans_date = trans['date']
                    cursor.execute("""
                        SELECT c.fy_id, fy.start_year, fy.end_year, COUNT(*)
                        FROM cases c
                        JOIN financial_years fy ON c.fy_id = fy.id
                        WHERE c.list != 'Deleted Cases'
                          AND ? BETWEEN fy.start_year AND fy.end_year
                        GROUP BY c.fy_id, fy.start_year, fy.end_year
                    """, (trans_date.year,))
                    matching_fys = cursor.fetchall()
                    if matching_fys:
                        print(f"DEBUG: Transaction date {trans_date} matches FYs: {matching_fys}")
                        # Use the first matching FY for duplicate checking
                        if fy_id != matching_fys[0][0]:
                            print(f"DEBUG: Switching to FY ID {matching_fys[0][0]} for duplicate checking")
                            fy_id = matching_fys[0][0]
                        break

            print(f"DEBUG: Current FY: {fy} (ID: {fy_id})")

            # First, let's see what cases exist in the database for this FY
            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE fy_id = ? AND list != 'Deleted Cases'
            """, (fy_id,))
            total_cases = cursor.fetchone()[0]
            print(f"DEBUG: Total cases in database for FY {fy}: {total_cases}")

            # Show a sample of existing cases
            cursor.execute("""
                SELECT transaction_no, responsibility_id, category, amount, list, fy_id
                FROM cases
                WHERE fy_id = ? AND list != 'Deleted Cases'
                LIMIT 5
            """, (fy_id,))
            sample_cases = cursor.fetchall()
            print(f"DEBUG: Sample existing cases in FY {fy} (ID: {fy_id}): {sample_cases}")

            # Also check if there are cases in other financial years
            cursor.execute("""
                SELECT fy_id, COUNT(*) FROM cases
                WHERE list != 'Deleted Cases'
                GROUP BY fy_id
            """)
            fy_counts = cursor.fetchall()
            print(f"DEBUG: Cases by financial year: {fy_counts}")

            # Check all cases regardless of FY
            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE list != 'Deleted Cases'
            """)
            total_all_cases = cursor.fetchone()[0]
            print(f"DEBUG: Total cases in all FYs (excluding deleted): {total_all_cases}")

            # Search for cases with same responsibility, category, amount, and financial year
            # First, find responsibility ID by name
            resp_id = None
            cursor.execute("SELECT id FROM responsibilities WHERE name = ?", (transaction['responsibility'],))
            resp_result = cursor.fetchone()
            resp_id = resp_result[0] if resp_result else None

            print(f"DEBUG: Looking for responsibility '{transaction['responsibility']}' - found ID: {resp_id}")
            print(f"DEBUG: Transaction details: responsibility='{transaction['responsibility']}', category='{self.category['name']}', amount={abs(transaction['amount']):.2f}")

            # Debug: Check what cases exist for this responsibility in the database
            if resp_id:
                cursor.execute("""
                    SELECT COUNT(*), GROUP_CONCAT(transaction_no, ', ') FROM cases
                    WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
                """, (resp_id, fy_id))
                resp_count, resp_cases = cursor.fetchone()
                print(f"DEBUG: Cases for responsibility ID {resp_id} in FY {fy}: {resp_count} cases")
                if resp_cases:
                    print(f"DEBUG: Sample case numbers: {resp_cases[:200]}...")

                # Check cases for this responsibility in ALL financial years
                cursor.execute("""
                    SELECT fy_id, COUNT(*), GROUP_CONCAT(transaction_no, ', ') FROM cases
                    WHERE responsibility_id = ? AND list != 'Deleted Cases'
                    GROUP BY fy_id
                """, (resp_id,))
                all_fy_resp_cases = cursor.fetchall()
                print(f"DEBUG: Cases for responsibility ID {resp_id} in ALL FYs: {all_fy_resp_cases}")

                # Check what lists the cases are in
                cursor.execute("""
                    SELECT list, COUNT(*) FROM cases
                    WHERE responsibility_id = ? AND fy_id = ?
                    GROUP BY list
                """, (resp_id, fy_id))
                list_counts = cursor.fetchall()
                print(f"DEBUG: Cases for responsibility ID {resp_id} by list in FY {fy}: {list_counts}")

                # Check the actual responsibility names in existing cases
                cursor.execute("""
                    SELECT DISTINCT r.name, COUNT(c.id) FROM cases c
                    JOIN responsibilities r ON c.responsibility_id = r.id
                    WHERE c.fy_id = ? AND c.list != 'Deleted Cases'
                    GROUP BY r.name
                    LIMIT 10
                """, (fy_id,))
                resp_names_in_cases = cursor.fetchall()
                print(f"DEBUG: Responsibility names in existing cases (FY {fy}): {resp_names_in_cases}")

                # Debug: Check category matching
                cursor.execute("""
                    SELECT COUNT(*) FROM cases
                    WHERE responsibility_id = ? AND category = ? AND fy_id = ? AND list != 'Deleted Cases'
                """, (resp_id, self.category['name'], fy_id))
                cat_count = cursor.fetchone()[0]
                print(f"DEBUG: Cases with matching category '{self.category['name']}': {cat_count}")

                # Debug: Check amount matching (broader range)
                transaction_amount = abs(transaction['amount'])
                cursor.execute("""
                    SELECT COUNT(*), MIN(amount), MAX(amount) FROM cases
                    WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
                """, (resp_id, fy_id))
                amt_count, min_amt, max_amt = cursor.fetchone()

                # Handle None values for min/max amounts when no cases exist
                min_amt_str = f"{min_amt:.2f}" if min_amt is not None else "N/A"
                max_amt_str = f"{max_amt:.2f}" if max_amt is not None else "N/A"
                print(f"DEBUG: Amount range for responsibility: {min_amt_str} - {max_amt_str} (transaction: {transaction_amount:.2f})")

            if resp_id:
                # Only return exact matches (same responsibility, category, amount, FY)
                # Debug: Check the transaction amount type and value
                print(f"DEBUG: Transaction amount raw: {transaction['amount']} (type: {type(transaction['amount'])})")

                # Ensure amount is numeric
                try:
                    if isinstance(transaction['amount'], str):
                        # Remove currency symbols and clean the string
                        amount_str = transaction['amount'].replace('R', '').replace(',', '').strip()
                        transaction_amount = abs(float(amount_str))
                    else:
                        transaction_amount = abs(float(transaction['amount']))
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error converting amount: {e}")
                    transaction_amount = 0.0

                print(f"DEBUG: Using transaction amount: {transaction_amount:.2f}")
                duplicates = []

                # First try exact match in current FY
                cursor.execute("""
                    SELECT * FROM cases
                    WHERE responsibility_id = ?
                      AND category = ?
                      AND ABS(amount - ?) < 0.01
                      AND fy_id = ?
                      AND list != 'Deleted Cases'
                """, (resp_id, self.category['name'], transaction_amount, fy_id))

                rows = cursor.fetchall()
                print(f"DEBUG: Exact match in current FY {fy_id} found {len(rows)} duplicates")
                if len(rows) > 0:
                    print(f"DEBUG: Exact match sample: {rows[0][1]} | {rows[0][9]} | {rows[0][11]:.2f}")
                    # Convert all rows to dictionaries
                    for row in rows:
                        case_dict = {
                            'id': row[0],
                            'transaction_no': row[1],
                            'date_incurred': row[2],
                            'date_identified': row[3],
                            'date_reported': row[4],
                            'description': row[5],
                            'bas_payment_no': row[6],
                            'bas_payment_date': row[7],
                            'persal_no': row[8],
                            'category': row[9],
                            'responsibility_id': row[10],
                            'amount': row[11],
                            'source_document': row[12],
                            'minutes': row[13],
                            'evidence_path': row[14],
                            'attachments': row[15],
                            'status': row[16],
                            'list': row[17],
                            'assessment_assessed_by': row[18],
                            'assessment_date': row[19],
                            'assessment_result': row[20],
                            'fy_id': row[21],
                            'period_id': row[22],
                            'criminal_charges': row[23],
                            'disciplinary_process': row[24],
                            'loss_recovery': row[25],
                            'prevention_steps': row[26],
                            'original_list': row[27]
                        }
                        duplicates.append(case_dict)
                else:
                    # If no matches in current FY, check orphaned FYs
                    for orphaned_fy_id in orphaned_fy_ids:
                        print(f"DEBUG: Checking orphaned FY {orphaned_fy_id} for duplicates")
                        cursor.execute("""
                            SELECT * FROM cases
                            WHERE responsibility_id = ?
                              AND category = ?
                              AND ABS(amount - ?) < 0.01
                              AND fy_id = ?
                              AND list != 'Deleted Cases'
                        """, (resp_id, self.category['name'], transaction_amount, orphaned_fy_id))

                        orphaned_rows = cursor.fetchall()
                        print(f"DEBUG: Exact match in orphaned FY {orphaned_fy_id} found {len(orphaned_rows)} duplicates")
                        if len(orphaned_rows) > 0:
                            print(f"DEBUG: Orphaned FY match sample: {orphaned_rows[0][1]} | {orphaned_rows[0][9]} | {orphaned_rows[0][11]:.2f}")
                            # Convert orphaned rows to dictionaries too
                            for row in orphaned_rows:
                                case_dict = {
                                    'id': row[0],
                                    'transaction_no': row[1],
                                    'date_incurred': row[2],
                                    'date_identified': row[3],
                                    'date_reported': row[4],
                                    'description': row[5],
                                    'bas_payment_no': row[6],
                                    'bas_payment_date': row[7],
                                    'persal_no': row[8],
                                    'category': row[9],
                                    'responsibility_id': row[10],
                                    'amount': row[11],
                                    'source_document': row[12],
                                    'minutes': row[13],
                                    'evidence_path': row[14],
                                    'attachments': row[15],
                                    'status': row[16],
                                    'list': row[17],
                                    'assessment_assessed_by': row[18],
                                    'assessment_date': row[19],
                                    'assessment_result': row[20],
                                    'fy_id': row[21],
                                    'period_id': row[22],
                                    'criminal_charges': row[23],
                                    'disciplinary_process': row[24],
                                    'loss_recovery': row[25],
                                    'prevention_steps': row[26],
                                    'original_list': row[27]
                                }
                                duplicates.append(case_dict)
                            break  # Stop after finding matches in first orphaned FY

                    if not duplicates:
                        print(f"DEBUG: No exact matches found for: resp_id={resp_id}, category='{self.category['name']}', amount={transaction_amount:.2f}, fy_id={fy_id} or orphaned FYs")

                print(f"DEBUG: Total exact duplicates found: {len(duplicates)}")

                conn.close()
                return duplicates
            else:
                print(f"DEBUG: No responsibility ID found for '{transaction['responsibility']}' - cannot search for duplicates")
                conn.close()
                return []

        except sqlite3.Error as e:
            print(f"Error finding duplicates: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return []

    def assign_case_numbers(self):
        """Assign case numbers to all transactions"""
        if not self.transactions:
            QMessageBox.warning(self, "No Transactions", "No transactions to assign case numbers to")
            return

        try:
            # Get financial year
            fy = get_financial_year()

            # Get the current highest case number (don't increment yet)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Extract the ending year from financial year (e.g., "2025-2026" -> 2026)
            fy_end_year = int(fy.split('-')[1])

            # Get the highest existing case number for this financial year
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(transaction_no, 5) AS INTEGER))
                FROM cases
                WHERE transaction_no LIKE ?
            """, (f"{fy_end_year}%",))

            max_existing = cursor.fetchone()[0]
            current_counter = max_existing or 0
            conn.close()

            # Filter out transactions marked for removal before assigning case numbers
            transactions_to_assign = [t for t in self.transactions if not t.get('marked_for_removal', False)]

            # Assign preview case numbers (don't increment database counter yet)
            for i, transaction in enumerate(transactions_to_assign):
                preview_number = current_counter + i + 1
                case_number = f"{fy_end_year}{preview_number:05d}"
                transaction['case_number'] = case_number

            # Store the next counter value for when import actually happens
            self.next_counter_value = current_counter + len(transactions_to_assign)

            # Update the table to show case numbers
            self.populate_transactions_table()

            # Keep import button enabled and disable assign button
            self.import_button.setEnabled(True)
            self.assign_case_numbers_button.setEnabled(False)
            self.assign_case_numbers_button.setText("Case Numbers Assigned")

            QMessageBox.information(
                self, "Case Numbers Assigned",
                f"✅ Case numbers have been assigned to {len(transactions_to_assign)} transactions "
                f"(out of {len(self.transactions)} total).\n\n"
                f"Next available case number: {fy_end_year}{(current_counter + len(transactions_to_assign) + 1):05d}\n\n"
                "You can now proceed with importing the cases."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assign case numbers:\n{str(e)}")

    def import_cases(self):
        """Import cases using the worker thread"""
        if not self.transactions:
            QMessageBox.warning(self, "No Transactions", "No transactions to import")
            return

        # Filter out transactions marked for removal before checking case numbers
        transactions_to_import = [t for t in self.transactions if not t.get('marked_for_removal', False)]

        if not transactions_to_import:
            QMessageBox.warning(self, "No Transactions", "All transactions have been marked for removal. Nothing to import.")
            return

        # Check if case numbers have been assigned to transactions that will actually be imported
        transactions_without_case_numbers = [t for t in transactions_to_import if not t.get('case_number')]
        if transactions_without_case_numbers:
            QMessageBox.warning(
                self, "Case Numbers Required",
                f"{len(transactions_without_case_numbers)} transactions do not have case numbers assigned.\n\n"
                "Please click 'Assign Case Numbers' before importing cases."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Import",
            f"Import {len(transactions_to_import)} transactions as cases?\n\n"
            f"Date Range: {self.date_from.strftime('%d/%m/%Y')} to {self.date_to.strftime('%d/%m/%Y')}\n"
            "This will create new cases in the system.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.perform_import()

    def perform_import(self):
        """Perform the actual import using the worker thread"""
        # Filter out transactions marked for removal (already done in import_cases, but being safe)
        transactions_to_import = [t for t in self.transactions if not t.get('marked_for_removal', False)]

        if not transactions_to_import:
            QMessageBox.warning(self, "No Transactions", "All transactions have been marked for removal. Nothing to import.")
            return

        print(f"DEBUG: Starting import with {len(transactions_to_import)} transactions (filtered from {len(self.transactions)})")

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_button.setEnabled(False)

        self.worker = ImportWorker(transactions_to_import, self.category,
                                    self.date_from, self.date_to, self.bas_file_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.import_finished)
        self.worker.error.connect(self.import_error)
        self.worker.start()

    def update_progress(self, percentage, message):
        self.progress_bar.setValue(percentage)
        self.results_label.setText(message)

    def import_finished(self, imported_cases):
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Import Complete",
            f"Successfully imported {len(imported_cases)} cases:\n\n" +
            "\n".join(imported_cases[:10]) +  # Show first 10
            (f"\n... and {len(imported_cases) - 10} more" if len(imported_cases) > 10 else "")
        )
        self.accept()

    def import_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.import_button.setEnabled(True)
        QMessageBox.critical(self, "Import Error", f"Failed to import cases:\n{error_msg}")


# Function to launch the import dialog
def import_undisclosed_cases(parent=None):
    dialog = ImportUndisclosedCasesDialog(parent)
    return dialog.exec_()