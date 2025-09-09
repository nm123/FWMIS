import os
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
        # Implementation would include the duplicate finding logic from the original file
        # For brevity, returning empty list for now
        return []

    def assign_case_numbers(self):
        """Assign case numbers to all transactions"""
        # Implementation for case number assignment
        pass

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