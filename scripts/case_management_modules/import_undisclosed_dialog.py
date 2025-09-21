import sqlite3
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
from ..Utilities.config import DB_PATH
from ..models.bas_parser import BASParser
from ..category_management import ManageCategoriesDialog
from ..responsibility_management_ui import ResponsibilityManagementDialog
from ..responsibility_management_actions import edit_responsibility_by_name
from ..ui.dialogs.transaction_details_dialog import TransactionDetailsDialog
from ..Utilities.utils import format_currency_amount
from .duplicate_comparison_dialog import DuplicateComparisonDialog
from ..ui.components.import_undisclosed_ui import setup_ui
from .import_undisclosed_logic import ImportLogic
from ..Utilities.import_undisclosed_utils import validate_responsibility


class ImportUndisclosedCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 FWMIS - Import Undisclosed Cases from BAS Report")
        self.setFixedSize(1450, 900)
        self.setWindowIconText("📊")

        self.parser = BASParser()
        self.worker = None
        self.transactions = []
        self.category = None
        self.date_from = None
        self.date_to = None
        self.bas_file_path = None
        self.selected_fy = None

        # Initialize logic
        self.logic = ImportLogic(self)

        setup_ui(self)

    def browse_file(self):
        from PyQt5.QtWidgets import QFileDialog
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
            resp_item.setForeground(QColor.blue)  # Make it blue to indicate it's clickable
            font = resp_item.font()
            font.setUnderline(True)  # Underline to show it's a link
            resp_item.setFont(font)

            # Apply removal styling if marked for removal
            if is_marked_for_removal:
                resp_item.setBackground(QColor.red)
                resp_item.setForeground(QColor.white)
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
            resp_status = validate_responsibility(transaction['responsibility'])
            status_item = QTableWidgetItem(resp_status['status'])
            if resp_status['status'] == "Not Found":
                status_item.setBackground(QColor.red)
            elif resp_status['status'] == "Non-Posting":
                status_item.setBackground(QColor.yellow)
            else:
                status_item.setBackground(QColor.green)
            self.transactions_table.setItem(row, 5, status_item)

            # Duplicate Status
            dup_status = "Not Checked"
            has_duplicates = False
            if hasattr(self.logic, 'duplicate_check_results') and i < len(self.logic.duplicate_check_results):
                result = self.logic.duplicate_check_results[i]
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
                dup_item.setBackground(QColor.yellow)  # Highlight duplicates in yellow
                dup_item.setForeground(QColor.black)
            elif is_marked_for_removal:
                dup_item.setBackground(QColor.red)
                dup_item.setForeground(QColor.white)
            self.transactions_table.setItem(row, 6, dup_item)

            # Also highlight the entire row if it has duplicates
            if has_duplicates:
                for col in range(self.transactions_table.columnCount()):
                    item = self.transactions_table.item(row, col)
                    if item:
                        item.setBackground(QColor.yellow)
                        item.setForeground(QColor.black)

            # Apply removal styling to entire row if marked for removal
            if is_marked_for_removal:
                for col in range(self.transactions_table.columnCount()):
                    item = self.transactions_table.item(row, col)
                    if item:
                        item.setBackground(QColor.red)
                        item.setForeground(QColor.white)

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

    def manage_responsibilities(self):
        dialog = ResponsibilityManagementDialog(self)
        dialog.exec_()
        # Refresh validation status after potential changes

    def compare_duplicates(self, transaction, duplicates):
        """Open duplicate comparison dialog"""
        # Create a copy of the transaction with category name for display
        transaction_copy = transaction.copy()
        transaction_copy['category_name'] = self.category['name'] if self.category else 'N/A'

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

    def check_duplicates(self):
        self.logic.check_duplicates()

    def assign_case_numbers(self):
        self.logic.assign_case_numbers()

    def import_cases(self):
        self.logic.import_cases()

    def update_progress(self, percentage, message):
        self.progress_bar.setValue(percentage)
        self.results_label.setText(message)

    def import_finished(self, imported_cases):
        self.progress_bar.setVisible(False)

        # Update the database counter to reflect the imported case numbers
        if imported_cases:
            try:
                from scripts.Utilities.financial_utils import get_financial_year
                fy = get_financial_year()
                fy_end_year = int(fy.split('-')[1])

                print(f"DEBUG: import_finished - updating counter for FY: {fy}")
                print(f"DEBUG: import_finished - imported_cases: {imported_cases[:3]}...")  # Show first 3

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get the highest number from the imported cases
                max_imported = max(int(case.split(str(fy_end_year))[1]) for case in imported_cases)
                print(f"DEBUG: import_finished - max_imported: {max_imported}")

                # Check current counter before update
                cursor.execute("""
                    SELECT counter FROM fy_case_counters WHERE fy_id = (
                        SELECT id FROM financial_years WHERE start_year = ?
                    )
                """, (fy_end_year - 1,))
                old_counter = cursor.fetchone()
                print(f"DEBUG: import_finished - old_counter: {old_counter}")

                # Update the counter to the next available number
                new_counter = max_imported + 1
                cursor.execute("""
                    UPDATE fy_case_counters SET counter = ? WHERE fy_id = (
                        SELECT id FROM financial_years WHERE start_year = ?
                    )
                """, (new_counter, fy_end_year - 1))

                print(f"DEBUG: import_finished - updated counter to: {new_counter}")

                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning: Could not update case counter: {e}")
                import traceback
                print(f"DEBUG: Counter update traceback: {traceback.format_exc()}")

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