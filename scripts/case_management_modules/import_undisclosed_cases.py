import os
import sqlite3
import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QDateEdit, QFileDialog, QMessageBox, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QProgressBar, QGroupBox, QTextEdit, QComboBox, QCheckBox
)
from PyQt5.QtCore import QDate, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year, generate_transaction_no, create_year_folder
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.responsibility_utils import load_posting_responsibilities
from scripts.Utilities.category_utils import load_categories
from scripts.category_management import ManageCategoriesDialog
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.responsibility_management_actions import edit_responsibility_by_name
from .duplicate_comparison_dialog import DuplicateComparisonDialog
from scripts.Utilities.utils import format_currency_amount


class BASParser:
    """Parser for BAS report files"""

    def __init__(self):
        self.transactions = []
        self.extracted_date_from = None
        self.extracted_date_to = None

    def extract_dates_from_header(self, lines):
        """Extract date range from BAS report header"""
        self.extracted_date_from = None
        self.extracted_date_to = None

        # Look for various date range patterns in header lines (first 30 lines)
        patterns = [
            re.compile(r'(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})'),  # 01/05/2025 TO 31/05/2025
            re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'),   # 01/05/2025 - 31/05/2025
            re.compile(r'FROM\s+(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})'),  # FROM 01/05/2025 TO 31/05/2025
            re.compile(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})'),     # 01/05/2025 31/05/2025
        ]

        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    try:
                        date_from_str = match.group(1)
                        date_to_str = match.group(2)

                        # Parse dates (DD/MM/YYYY format)
                        self.extracted_date_from = datetime.strptime(date_from_str, '%d/%m/%Y').date()
                        self.extracted_date_to = datetime.strptime(date_to_str, '%d/%m/%Y').date()
                        return  # Exit early once we find dates
                    except ValueError:
                        continue

        # If no standard patterns found, try to find any date ranges in the file
        date_only_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})')
        found_dates = []

        for line in lines[:100]:
            matches = date_only_pattern.findall(line)
            if matches:
                found_dates.extend(matches)

        if len(found_dates) >= 2:
            try:
                # Take first two dates as from/to range
                self.extracted_date_from = datetime.strptime(found_dates[0], '%d/%m/%Y').date()
                self.extracted_date_to = datetime.strptime(found_dates[1], '%d/%m/%Y').date()
                return
            except ValueError:
                pass

    def parse_file(self, file_path, date_from, date_to):
        """Parse BAS report file and extract transactions"""
        self.transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Extract dates from header first
            self.extract_dates_from_header(lines)

            current_responsibility = None
            current_item = None

            for line in lines:
                line = line.rstrip()

                # Check for responsibility line (R 007)
                resp_match = re.match(r'\s*R\s+(\d+)\s+(.+)', line)
                if resp_match:
                    current_responsibility = resp_match.group(2).strip()
                    continue

                # Check for item line (I 005) - exclude amounts at the end
                item_match = re.match(r'\s*I\s+(\d+)\s+(.+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s*$', line)
                if item_match:
                    current_item = item_match.group(2).strip()
                    continue

                # Check for transaction lines (AP, GJ, CL)
                # Updated regex to handle system-generated numbers before actual user names
                trans_match = re.match(r'\s*(AP|GJ|CL)\s+(\d+)\s+(.+?)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})', line)
                if trans_match and current_responsibility and current_item:
                    trans_type = trans_match.group(1)
                    trans_number = trans_match.group(2)
                    description = trans_match.group(3).strip()
                    # Extract the last word as the actual user name (handles system-generated numbers)
                    user_field = trans_match.group(4).strip()
                    user_name = user_field.split()[-1] if user_field else ""  # Get the last word (actual user name)
                    user_date = trans_match.group(5)
                    debit = trans_match.group(6).replace(',', '')
                    credit = trans_match.group(7).replace(',', '')

                    # Parse date (DD/MM/YYYY format)
                    try:
                        date_obj = datetime.strptime(user_date, '%d/%m/%Y').date()
                    except ValueError:
                        continue  # Skip invalid dates

                    # Validate date range (skip if dates are None - used for header extraction)
                    if date_from is not None and date_to is not None:
                        if not (date_from <= date_obj <= date_to):
                            continue

                    # Determine amount (debit or credit)
                    try:
                        amount = float(debit) if float(debit) > 0 else -float(credit)
                    except ValueError:
                        continue

                    # Create transaction record
                    transaction = {
                        'responsibility': current_responsibility,
                        'item': current_item,
                        'type': trans_type,
                        'number': trans_number,
                        'description': description,
                        'date': date_obj,
                        'user_id': user_name,  # Use the actual user name instead of system-generated number
                        'amount': amount,
                        'is_credit': amount < 0
                    }

                    self.transactions.append(transaction)

        except Exception as e:
            raise Exception(f"Error parsing BAS file: {str(e)}")

        return self.transactions

    def get_extracted_dates(self):
        """Get the extracted date range from the report header"""
        return {
            'date_from': self.extracted_date_from,
            'date_to': self.extracted_date_to
        }

    def get_transaction_summary(self):
        """Get summary of parsed transactions"""
        if not self.transactions:
            return "No transactions found"

        total_count = len(self.transactions)
        debit_count = len([t for t in self.transactions if not t['is_credit']])
        credit_count = len([t for t in self.transactions if t['is_credit']])
        total_amount = sum(abs(t['amount']) for t in self.transactions)

        return f"Found {total_count} transactions ({debit_count} debits, {credit_count} credits) totaling {format_currency_amount(total_amount)}"


class ImportWorker(QThread):
    """Worker thread for importing cases"""
    progress = pyqtSignal(int, str)  # progress percentage, current operation
    finished = pyqtSignal(list)  # list of imported case numbers
    error = pyqtSignal(str)

    def __init__(self, transactions, category, date_from, date_to, bas_file_path):
        super().__init__()
        self.transactions = transactions
        self.category = category
        self.date_from = date_from
        self.date_to = date_to
        self.bas_file_path = bas_file_path

    def run(self):
        try:
            imported_cases = []
            total = len(self.transactions)
            print(f"DEBUG: ImportWorker starting with {total} transactions")

            for i, transaction in enumerate(self.transactions):
                self.progress.emit(int((i / total) * 100), f"Importing case {i+1} of {total}...")
                print(f"DEBUG: Processing transaction {i+1}: {transaction.get('case_number', 'No case number')}")

                # Import the transaction as a case
                case_number = self._import_transaction(transaction)
                if case_number:
                    imported_cases.append(case_number)
                    print(f"DEBUG: Successfully imported case: {case_number}")
                else:
                    print(f"DEBUG: Failed to import transaction {i+1}")

            print(f"DEBUG: Import completed. Successfully imported {len(imported_cases)} cases")
            self.progress.emit(100, "Import completed successfully")
            self.finished.emit(imported_cases)

        except Exception as e:
            print(f"DEBUG: ImportWorker error: {e}")
            self.error.emit(str(e))

    def _import_transaction(self, transaction):
        """Import a single transaction as a case"""
        try:
            print(f"DEBUG: _import_transaction called for: {transaction.get('case_number', 'No case number')}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Get financial year ID
            cursor.execute("SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?", (start_year, end_year))
            fy_result = cursor.fetchone()
            fy_id = fy_result[0] if fy_result else None

            print(f"DEBUG: Import - Current FY: {fy}, start_year: {start_year}, end_year: {end_year}, fy_id: {fy_id}")

            # CRITICAL: Check if fy_id is valid before proceeding
            if fy_id is None:
                print(f"DEBUG: *** CRITICAL ERROR *** FY {fy} not found in database!")
                print(f"DEBUG: This will cause cases to be imported with invalid fy_id")
                conn.close()
                raise Exception(f"Financial Year {fy} not found in database. Please ensure the financial year is properly set up in Financial Year Management before importing cases.")
            else:
                print(f"DEBUG: Found FY {fy} with ID: {fy_id}")

            # Get period ID for the transaction date
            period_id = None
            if fy_id:
                # Convert transaction date to string format for database query
                date_str = transaction['date'].strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT id FROM periods
                    WHERE fy_id = ? AND start_date <= ? AND end_date >= ?
                    ORDER BY period_number DESC LIMIT 1
                """, (fy_id, date_str, date_str))
                period_result = cursor.fetchone()
                period_id = period_result[0] if period_result else None

                # If no period found for this date, try to find the most recent open period for this FY
                if period_id is None:
                    cursor.execute("""
                        SELECT id FROM periods
                        WHERE fy_id = ? AND status = 'open'
                        ORDER BY period_number DESC LIMIT 1
                    """, (fy_id,))
                    open_period_result = cursor.fetchone()
                    if open_period_result:
                        period_id = open_period_result[0]
                        print(f"DEBUG: Using open period {period_id} for FY {fy_id} as fallback")
                    else:
                        print(f"DEBUG: No open periods found for FY {fy_id}, using period_id = None")

            # Get responsibility ID
            resp_id = None
            cursor.execute("SELECT id FROM responsibilities WHERE name = ?", (transaction['responsibility'],))
            resp_result = cursor.fetchone()
            resp_id = resp_result[0] if resp_result else None

            # Debug: Log responsibility lookup result
            if resp_id:
                print(f"DEBUG: Found responsibility '{transaction['responsibility']}' with ID: {resp_id}")
            else:
                print(f"DEBUG: Responsibility '{transaction['responsibility']}' NOT found in database")

            # Use the case number that was already assigned during preview
            case_number = transaction.get('case_number')
            if not case_number:
                print("DEBUG: No case number assigned, using fallback")
                # Fallback if no case number was assigned
                cursor.execute("SELECT MAX(CAST(SUBSTR(transaction_no, 5) AS INTEGER)) FROM cases WHERE transaction_no LIKE ?", (f"{fy}%",))
                max_num = cursor.fetchone()[0]
                next_num = (max_num or 0) + 1
                fy_end_year = int(fy.split('-')[1])
                case_number = f"{fy_end_year}{next_num:05d}"

            print(f"DEBUG: Using case number: {case_number}, fy_id: {fy_id}, period_id: {period_id}, resp_id: {resp_id}")

            # Prepare case data
            # date_str already defined above for period lookup

            # Debug: Log the actual values being inserted
            print(f"DEBUG: Inserting case with values:")
            print(f"  - transaction_no: {case_number}")
            print(f"  - responsibility_id: {resp_id}")
            print(f"  - category: {self.category['name']}")
            print(f"  - amount: {abs(transaction['amount'])}")
            print(f"  - fy_id: {fy_id}")
            print(f"  - period_id: {period_id}")

            # Determine list and status based on transaction type
            if transaction['type'] == 'GJ':
                list_name = 'Checklist'  # Will also be added to To-Do List
                status = 'Alleged'
            else:  # CL or AP
                list_name = 'Checklist'
                status = 'Alleged'

            # Clean transaction number
            clean_number = transaction['number'].lstrip('0') or '0'

            # Prepare description
            if transaction['type'] == 'GJ':
                description = f"{transaction['item']}. Journal authorised by BAS user {transaction['user_id']}"
                bas_journal_no = clean_number
                bas_journal_date = date_str
                bas_payment_no = None
                bas_payment_date = None
            elif transaction['type'] == 'AP':
                description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                bas_journal_no = None
                bas_journal_date = None
                bas_payment_no = clean_number
                bas_payment_date = date_str
            else:  # CL
                description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                bas_journal_no = None
                bas_journal_date = None
                bas_payment_no = clean_number
                bas_payment_date = date_str

            # Get default list ID
            cursor.execute("SELECT id FROM lists WHERE name = ? AND is_default = 1", (list_name,))
            list_result = cursor.fetchone()
            list_id = list_result[0] if list_result else 1

            # Insert case - ensure NULL values are properly handled
            cursor.execute("""
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported,
                    description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category,
                    responsibility_id, amount, source_document, minutes, evidence_path,
                    attachments, status, list, assessment_assessed_by, assessment_date,
                    assessment_result, fy_id, period_id, criminal_charges, disciplinary_process,
                    loss_recovery, prevention_steps, original_list
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_number, date_str, date_str, date_str,
                description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, None, self.category['name'],
                resp_id, abs(transaction['amount']), None, None, None,  # Will set evidence later
                '[]', status, list_name, None, None,
                fy_id, period_id, 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', list_name
            ))

            case_id = cursor.lastrowid

            # Debug: Verify what was actually saved
            cursor.execute("SELECT responsibility_id FROM cases WHERE id = ?", (case_id,))
            saved_resp_id = cursor.fetchone()
            print(f"DEBUG: Case {case_number} saved with responsibility_id: {saved_resp_id[0] if saved_resp_id else 'None'}")


            # Copy BAS file to proper location (not as evidence)
            if self.bas_file_path:
                # Create Imported BAS Files folder structure
                year_folder = create_year_folder(fy)
                bas_files_folder = os.path.join(year_folder, "Imported BAS Files")

                # Extract month from transaction date for subfolder (e.g., "202505")
                month_str = transaction['date'].strftime('%Y%m')
                month_folder = os.path.join(bas_files_folder, month_str)

                # Create directories
                os.makedirs(month_folder, exist_ok=True)

                # Get original filename and copy with correct extension
                original_filename = os.path.basename(self.bas_file_path)
                bas_file_path = os.path.join(month_folder, original_filename)

                # Copy file
                import shutil
                shutil.copy2(self.bas_file_path, bas_file_path)

                # Store BAS file path in source_document field instead of evidence_path
                cursor.execute("UPDATE cases SET source_document = ? WHERE transaction_no = ?",
                              (bas_file_path, case_number))

                print(f"DEBUG: Copied BAS file to: {bas_file_path}")

            print(f"DEBUG: About to commit transaction for case: {case_number}")
            conn.commit()
            conn.close()
            print(f"DEBUG: Successfully committed case: {case_number}")

            # Log audit (convert all date objects to strings for JSON serialization)
            def convert_dates(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates(item) for item in obj]
                elif hasattr(obj, 'isoformat'):  # Date/datetime objects
                    return obj.isoformat()
                else:
                    return obj

            audit_transaction = convert_dates(transaction)

            save_audit_log("import_undisclosed_case", {
                "timestamp": datetime.now().isoformat(),
                "case_number": case_number,
                "transaction": audit_transaction,
                "category": self.category['name']
            }, fy)

            return case_number

        except Exception as e:
            print(f"DEBUG: Error importing transaction: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            # Ensure database connection is properly closed on error
            if 'conn' in locals():
                try:
                    conn.rollback()  # Rollback any pending transaction
                    conn.close()
                except:
                    pass
            return None


class ImportUndisclosedCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Undisclosed Cases from BAS Report")
        self.setFixedSize(1400, 800)

        self.parser = BASParser()
        self.transactions = []
        self.category = None
        self.date_from = None
        self.date_to = None
        self.bas_file_path = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # File selection section
        file_group = QGroupBox("BAS Report File")
        file_layout = QHBoxLayout()

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select BAS report file...")
        self.file_path_edit.setReadOnly(True)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)

        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Category and date selection
        selection_group = QGroupBox("Import Settings")
        selection_layout = QHBoxLayout()

        # Category selection
        category_layout = QVBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_button = QPushButton("Select Category")
        self.category_button.clicked.connect(self.select_category)
        self.category_label = QLabel("No category selected")
        category_layout.addWidget(self.category_button)
        category_layout.addWidget(self.category_label)
        selection_layout.addLayout(category_layout)

        # Case destination info
        destination_layout = QVBoxLayout()
        destination_layout.addWidget(QLabel("Cases will be posted to:"))
        self.destination_info = QLabel()
        self.destination_info.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 3px;
                padding: 5px;
                color: #2E7D32;
                font-weight: bold;
            }
        """)
        self.destination_info.setText("📋 List: Checklist\n📊 Status: Alleged")
        self.destination_info.setToolTip("All imported cases will be assigned to the Checklist with Alleged status")
        destination_layout.addWidget(self.destination_info)
        selection_layout.addLayout(destination_layout)

        # Date range selection
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Date Range:"))

        date_range_layout = QHBoxLayout()
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.setCalendarPopup(True)
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setCalendarPopup(True)

        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.date_from_edit)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.date_to_edit)
        date_layout.addLayout(date_range_layout)
        selection_layout.addLayout(date_layout)

        # Parse button
        self.parse_button = QPushButton("Parse File")
        self.parse_button.clicked.connect(self.parse_file)
        self.parse_button.setEnabled(False)
        selection_layout.addWidget(self.parse_button)

        selection_layout.addStretch()
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # Results section
        results_group = QGroupBox("Parsed Transactions")
        results_layout = QVBoxLayout()

        self.results_label = QLabel("No file parsed yet")
        results_layout.addWidget(self.results_label)

        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(9)
        self.transactions_table.setHorizontalHeaderLabels([
            "Responsibility", "Type", "Amount", "Date", "Description", "Resp Status", "Dup Status", "Case Number", "Actions"
        ])
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.transactions_table.setColumnWidth(0, 180)  # Responsibility
        self.transactions_table.setColumnWidth(1, 60)   # Type
        self.transactions_table.setColumnWidth(2, 100)  # Amount
        self.transactions_table.setColumnWidth(3, 100)  # Date
        self.transactions_table.setColumnWidth(4, 200)  # Description
        self.transactions_table.setColumnWidth(5, 100)  # Resp Status
        self.transactions_table.setColumnWidth(6, 100)  # Dup Status
        self.transactions_table.setColumnWidth(7, 120)  # Case Number
        self.transactions_table.setColumnWidth(8, 120)  # Actions

        # Connect double-click signal for editing responsibilities
        self.transactions_table.itemDoubleClicked.connect(self.on_table_double_click)

        results_layout.addWidget(self.transactions_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()

        self.manage_resp_button = QPushButton("Manage Responsibilities")
        self.manage_resp_button.clicked.connect(self.manage_responsibilities)
        self.manage_resp_button.setEnabled(False)

        self.check_duplicates_button = QPushButton("Check Duplicates")
        self.check_duplicates_button.clicked.connect(self.check_duplicates)
        self.check_duplicates_button.setEnabled(False)

        self.assign_case_numbers_button = QPushButton("Assign Case Numbers")
        self.assign_case_numbers_button.clicked.connect(self.assign_case_numbers)
        self.assign_case_numbers_button.setEnabled(False)
        self.assign_case_numbers_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")

        self.import_button = QPushButton("Import Cases")
        self.import_button.clicked.connect(self.import_cases)
        self.import_button.setEnabled(False)
        self.import_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.manage_resp_button)
        button_layout.addWidget(self.check_duplicates_button)
        button_layout.addWidget(self.assign_case_numbers_button)
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

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
                self.category_label.setText(f"Selected: {selected['name']}")
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
            view_btn.clicked.connect(lambda checked, trans=transaction: self.view_transaction_details(trans))
            actions_layout.addWidget(view_btn)

            # Compare Duplicates button (only if duplicates exist)
            if has_duplicates:
                compare_btn = QPushButton("Compare")
                compare_btn.clicked.connect(lambda checked, trans=transaction, dups=result['duplicates']: self.compare_duplicates(trans, dups))
                compare_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
                actions_layout.addWidget(compare_btn)

            self.transactions_table.setCellWidget(row, 8, actions_widget)

        # Restore scroll position
        self.transactions_table.verticalScrollBar().setValue(vertical_scroll_pos)
        self.transactions_table.horizontalScrollBar().setValue(horizontal_scroll_pos)

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
                    duplicates.extend(rows)
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
                            duplicates.extend(orphaned_rows)
                            break  # Stop after finding matches in first orphaned FY

                    if not duplicates:
                        print(f"DEBUG: No exact matches found for: resp_id={resp_id}, category='{self.category['name']}', amount={transaction_amount:.2f}, fy_id={fy_id} or orphaned FYs")

                print(f"DEBUG: Total exact duplicates found: {len(duplicates)}")

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

    def analyze_database_vs_import_data(self):
        """Comprehensive analysis of database content vs import data"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get current financial year
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Get fy_id
            cursor.execute("SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?", (start_year, end_year))
            fy_result = cursor.fetchone()
            fy_id = fy_result[0] if fy_result else None

            print("\n" + "="*80)
            print("COMPREHENSIVE DATABASE VS IMPORT ANALYSIS")
            print("="*80)

            # 1. Database content analysis
            print(f"\n1. DATABASE CONTENT ANALYSIS (FY: {fy}, fy_id: {fy_id})")
            print("-" * 50)

            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE fy_id = ? AND list != 'Deleted Cases'
            """, (fy_id,))
            total_db_cases = cursor.fetchone()[0]
            print(f"Total cases in database: {total_db_cases}")

            # Get sample of database cases
            cursor.execute("""
                SELECT transaction_no, responsibility_id, category, amount, list, status
                FROM cases
                WHERE fy_id = ? AND list != 'Deleted Cases'
                ORDER BY transaction_no
                LIMIT 10
            """, (fy_id,))
            db_cases = cursor.fetchall()

            print("\nSample database cases:")
            for case in db_cases:
                print(f"  {case[0]} | RespID: {case[1]} | Cat: {case[2]} | Amt: {case[3]:.2f} | List: {case[4]} | Status: {case[5]}")

            # 2. Import data analysis
            print(f"\n2. IMPORT DATA ANALYSIS")
            print("-" * 50)
            print(f"Total transactions to import: {len(self.transactions)}")

            print("\nSample import transactions:")
            for i, transaction in enumerate(self.transactions[:10]):
                print(f"  {i+1}. Resp: '{transaction['responsibility']}' | Cat: '{self.category['name']}' | Amt: {abs(transaction['amount']):.2f}")

            # 3. Responsibility mapping analysis
            print(f"\n3. RESPONSIBILITY MAPPING ANALYSIS")
            print("-" * 50)

            # Get all unique responsibilities from import
            import_responsibilities = set(t['responsibility'] for t in self.transactions)
            print(f"Unique responsibilities in import: {len(import_responsibilities)}")
            for resp in sorted(list(import_responsibilities))[:10]:  # Show first 10
                print(f"  '{resp}'")

            # Check which responsibilities exist in database
            existing_resp_map = {}
            for resp_name in import_responsibilities:
                cursor.execute("SELECT id FROM responsibilities WHERE name = ?", (resp_name,))
                result = cursor.fetchone()
                existing_resp_map[resp_name] = result[0] if result else None

            print(f"\nResponsibility mapping (import -> database ID):")
            for resp_name, db_id in existing_resp_map.items():
                status = "✓" if db_id else "✗"
                print(f"  {status} '{resp_name}' -> ID: {db_id}")

            # 4. Category analysis
            print(f"\n4. CATEGORY ANALYSIS")
            print("-" * 50)
            print(f"Import category: '{self.category['name']}'")

            # Check if category exists
            cursor.execute("SELECT id FROM categories WHERE name = ?", (self.category['name'],))
            cat_result = cursor.fetchone()
            print(f"Category exists in database: {'✓' if cat_result else '✗'} (ID: {cat_result[0] if cat_result else 'None'})")

            # 5. Amount analysis
            print(f"\n5. AMOUNT ANALYSIS")
            print("-" * 50)

            import_amounts = [abs(t['amount']) for t in self.transactions]
            db_amounts = []

            cursor.execute("""
                SELECT amount FROM cases
                WHERE fy_id = ? AND list != 'Deleted Cases'
            """, (fy_id,))
            db_amount_rows = cursor.fetchall()
            db_amounts = [row[0] for row in db_amount_rows]

            print(f"Import amounts range: {min(import_amounts):.2f} - {max(import_amounts):.2f}")
            print(f"Database amounts range: {min(db_amounts):.2f} - {max(db_amounts):.2f}" if db_amounts else "No amounts in database")

            # 6. Potential matches analysis
            print(f"\n6. POTENTIAL MATCHES ANALYSIS")
            print("-" * 50)

            matches_found = 0
            for transaction in self.transactions[:5]:  # Check first 5 transactions
                resp_id = existing_resp_map.get(transaction['responsibility'])
                if resp_id:
                    cursor.execute("""
                        SELECT COUNT(*) FROM cases
                        WHERE responsibility_id = ?
                          AND fy_id = ?
                          AND list != 'Deleted Cases'
                    """, (resp_id, fy_id))
                    count = cursor.fetchone()[0]
                    if count > 0:
                        matches_found += 1
                        print(f"  ✓ Transaction '{transaction['responsibility']}' has {count} potential matches by responsibility")

            print(f"\nSUMMARY:")
            print(f"- Database cases: {total_db_cases}")
            print(f"- Import transactions: {len(self.transactions)}")
            print(f"- Responsibilities with DB matches: {sum(1 for v in existing_resp_map.values() if v is not None)}/{len(existing_resp_map)}")
            print(f"- Transactions with potential matches: {matches_found}/5 (sampled)")

            if matches_found == 0:
                print("\n⚠️  POTENTIAL ISSUES IDENTIFIED:")
                if sum(1 for v in existing_resp_map.values() if v is not None) == 0:
                    print("  - No responsibilities from import file exist in database")
                if total_db_cases == 0:
                    print("  - No cases exist in database for current financial year")
                print("  - Category mismatch possible")
                print("  - Amount precision/formatting differences")

            print("\n" + "="*80)

            conn.close()

        except Exception as e:
            print(f"Error in analysis: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

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

            # Assign preview case numbers (don't increment database counter yet)
            for i, transaction in enumerate(self.transactions):
                preview_number = current_counter + i + 1
                case_number = f"{fy_end_year}{preview_number:05d}"
                transaction['case_number'] = case_number

            # Store the next counter value for when import actually happens
            self.next_counter_value = current_counter + len(self.transactions)

            # Update the table to show case numbers
            self.populate_transactions_table()

            # Enable import button and disable assign button
            self.import_button.setEnabled(True)
            self.assign_case_numbers_button.setEnabled(False)
            self.assign_case_numbers_button.setText("Case Numbers Assigned")

            QMessageBox.information(
                self, "Case Numbers Assigned",
                f"✅ Case numbers have been assigned to all {len(self.transactions)} transactions.\n\n"
                f"Next available case number: {fy_end_year}{(current_counter + len(self.transactions) + 1):05d}\n\n"
                "You can now proceed with importing the cases."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assign case numbers:\n{str(e)}")

    def import_cases(self):
        if not self.transactions:
            QMessageBox.warning(self, "No Transactions", "No transactions to import")
            return

        # Check if the period is open
        period_status = self.check_period_status()
        if period_status['status'] == 'closed':
            # Get current open period
            current_period = self.get_current_open_period()

            if current_period:
                # Parse string dates back to datetime objects for formatting
                start_date = datetime.strptime(current_period['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(current_period['end_date'], '%Y-%m-%d').date()

                reply = QMessageBox.question(
                    self, "Closed Period - Action Required",
                    f"CRITICAL: The selected date range ({self.date_from.strftime('%d/%m/%Y')} to {self.date_to.strftime('%d/%m/%Y')}) falls within a CLOSED period.\n\n"
                    f"Closed Period: {period_status['period_name']}\n"
                    f"Status: {period_status['status'].title()}\n\n"
                    f"Available Open Period: Period {current_period['period_number']} "
                    f"({start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')})\n\n"
                    "Do you want to post these transactions to the current OPEN period instead?\n\n"
                    "WARNING: Transactions CANNOT be posted to closed periods.",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Use current open period dates
                    self.date_from = current_period['start_date']
                    self.date_to = current_period['end_date']
                    QMessageBox.information(
                        self, "Period Changed",
                        f"✅ Import dates changed to current open period:\n"
                        f"From: {self.date_from.strftime('%d/%m/%Y')}\n"
                        f"To: {self.date_to.strftime('%d/%m/%Y')}\n\n"
                        f"This ensures compliance and data integrity."
                    )
                else:
                    QMessageBox.warning(
                        self, "Import Cancelled",
                        "❌ Import cancelled to prevent posting to closed period.\n\n"
                        "Please open the appropriate period first or select dates within an open period."
                    )
                    return
            else:
                QMessageBox.critical(
                    self, "No Open Period Available",
                    "❌ CRITICAL: The selected dates fall within a closed period AND no open period is available.\n\n"
                    "Please open a period in Financial Year Management before importing transactions.\n\n"
                    "⚠️  Transactions cannot be posted to closed periods."
                )
                return

        elif period_status['status'] == 'not_found':
            QMessageBox.warning(
                self, "Period Not Found",
                f"⚠️  Warning: Could not determine period status for the selected date range.\n\n"
                f"Date Range: {self.date_from.strftime('%d/%m/%Y')} to {self.date_to.strftime('%d/%m/%Y')}\n\n"
                "Please verify the dates are within a valid financial period."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Import",
            f"Import {len(self.transactions)} transactions as cases?\n\n"
            f"Date Range: {self.date_from.strftime('%d/%m/%Y')} to {self.date_to.strftime('%d/%m/%Y')}\n"
            "This will create new cases in the system.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.perform_import()

    def perform_import(self):
        # Filter out transactions marked for removal
        transactions_to_import = [t for t in self.transactions if not t.get('marked_for_removal', False)]

        if not transactions_to_import:
            QMessageBox.warning(self, "No Transactions", "All transactions have been marked for removal. Nothing to import.")
            return

        print(f"DEBUG: Starting import with {len(transactions_to_import)} transactions (filtered from {len(self.transactions)})")
        for i, t in enumerate(transactions_to_import[:3]):  # Show first 3 for debugging
            print(f"DEBUG: Transaction {i+1}: {t['responsibility']} - {t['amount']} - Case: {t.get('case_number', 'No case number')}")

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

        # Update the database counter to reflect the imported case numbers
        if imported_cases:
            try:
                fy = get_financial_year()
                fy_end_year = int(fy.split('-')[1])

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get the highest number from the imported cases
                max_imported = max(int(case.split(str(fy_end_year))[1]) for case in imported_cases)

                # Update the counter to the next available number
                cursor.execute("""
                    UPDATE fy_case_counters SET counter = ? WHERE fy_id = (
                        SELECT id FROM financial_years WHERE start_year = ?
                    )
                """, (max_imported + 1, fy_end_year - 1))

                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning: Could not update case counter: {e}")

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

    def check_period_status(self):
        """Check if the period for the selected date range is open"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year for the date range
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Find the period that contains the date range
            cursor.execute("""
                SELECT p.id, p.period_number, p.status, p.start_date, p.end_date
                FROM periods p
                WHERE p.fy_id = (SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?)
                  AND p.start_date <= ? AND p.end_date >= ?
            """, (start_year, end_year, self.date_to, self.date_from))

            period = cursor.fetchone()
            conn.close()

            if period:
                return {
                    'id': period[0],
                    'period_number': period[1],
                    'status': period[2],
                    'start_date': period[3],
                    'end_date': period[4],
                    'period_name': f"Period {period[1]}"
                }
            else:
                return {'status': 'not_found', 'period_name': 'Unknown'}

        except sqlite3.Error as e:
            print(f"Error checking period status: {e}")
            return {'status': 'error', 'period_name': 'Error'}

    def get_current_open_period(self):
        """Get the current open period"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Find the currently open period
            cursor.execute("""
                SELECT id, period_number, start_date, end_date
                FROM periods
                WHERE fy_id = (SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?)
                  AND status = 'open'
                ORDER BY period_number DESC
                LIMIT 1
            """, (start_year, end_year))

            period = cursor.fetchone()
            conn.close()

            if period:
                return {
                    'id': period[0],
                    'period_number': period[1],
                    'start_date': period[2],
                    'end_date': period[3]
                }
            else:
                return None

        except sqlite3.Error as e:
            print(f"Error getting current open period: {e}")
            return None


class TransactionDetailsDialog(QDialog):
    """Dialog to show detailed transaction information"""

    def __init__(self, transaction, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Details")
        self.setFixedSize(600, 400)

        self.transaction = transaction
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Transaction details
        form_layout = QFormLayout()

        form_layout.addRow("Responsibility:", QLabel(self.transaction['responsibility']))
        form_layout.addRow("Item:", QLabel(self.transaction['item']))
        form_layout.addRow("Type:", QLabel(self.transaction['type']))
        form_layout.addRow("Transaction Number:", QLabel(self.transaction['number']))

        amount = self.transaction['amount']
        amount_str = format_currency_amount(amount)
        if self.transaction['is_credit']:
            amount_str += " (Credit)"
        else:
            amount_str += " (Debit)"
        form_layout.addRow("Amount:", QLabel(amount_str))

        form_layout.addRow("Date:", QLabel(self.transaction['date'].strftime('%Y-%m-%d')))
        form_layout.addRow("User ID:", QLabel(self.transaction['user_id']))

        layout.addLayout(form_layout)

        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        desc_edit = QTextEdit()
        desc_edit.setPlainText(self.transaction['description'])
        desc_edit.setReadOnly(True)
        desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(desc_edit)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


# Function to launch the import dialog
def import_undisclosed_cases(parent=None):
    dialog = ImportUndisclosedCasesDialog(parent)
    return dialog.exec_()