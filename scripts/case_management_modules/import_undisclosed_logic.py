import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from ..Utilities.config import DB_PATH
from ..Utilities.financial_utils import get_financial_year, generate_transaction_no
from ..Utilities.audit_utils import save_audit_log
from ..core.import_worker import ImportWorker
from ..Utilities.import_undisclosed_utils import find_duplicates, check_period_status, get_current_open_period, validate_financial_year, analyze_database_vs_import_data


class ImportLogic:
    def __init__(self, dialog):
        self.dialog = dialog
        self.duplicate_check_results = []

    def perform_import(self):
        # Filter out transactions marked for removal (already done in import_cases, but being safe)
        transactions_to_import = [t for t in self.dialog.transactions if not t.get('marked_for_removal', False)]

        if not transactions_to_import:
            QMessageBox.warning(self.dialog, "No Transactions", "All transactions have been marked for removal. Nothing to import.")
            return

        print(f"DEBUG: Starting import with {len(transactions_to_import)} transactions (filtered from {len(self.dialog.transactions)})")

        self.dialog.progress_bar.setVisible(True)
        self.dialog.progress_bar.setValue(0)
        self.dialog.import_button.setEnabled(False)

        self.dialog.worker = ImportWorker(transactions_to_import, self.dialog.category,
                                          self.dialog.date_from, self.dialog.date_to, self.dialog.bas_file_path, self.dialog.selected_fy)
        self.dialog.worker.progress.connect(self.dialog.update_progress)
        self.dialog.worker.finished.connect(self.dialog.import_finished)
        self.dialog.worker.error.connect(self.dialog.import_error)
        self.dialog.worker.start()

    def assign_case_numbers(self):
        """Assign case numbers to all transactions"""
        if not self.dialog.transactions:
            QMessageBox.warning(self.dialog, "No Transactions", "No transactions to assign case numbers to")
            return

        try:
            # Get financial year
            fy = get_financial_year()
            print(f"DEBUG: ===== ASSIGN CASE NUMBERS START =====")
            print(f"DEBUG: assign_case_numbers - get_financial_year() returned: {fy}")

            # Get the current highest case number (don't increment yet)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Extract the ending year from financial year (e.g., "2025-2026" -> 2026)
            fy_end_year = int(fy.split('-')[1])

            # Get the highest existing case number for this financial year
            # Use fy_id to ensure we're only looking at cases from the correct financial year
            # Also exclude cases with NULL or invalid fy_id
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(transaction_no, 5) AS INTEGER))
                FROM cases
                WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?
                )
                AND fy_id IS NOT NULL
                AND list != 'Deleted Cases'
            """, (fy_end_year - 1, fy_end_year))

            max_existing = cursor.fetchone()[0]
            current_counter = max_existing or 0

            print(f"DEBUG: assign_case_numbers - FY: {fy}, fy_end_year: {fy_end_year}")
            print(f"DEBUG: assign_case_numbers - max_existing: {max_existing}, current_counter: {current_counter}")

            # Also check the fy_case_counters table
            cursor.execute("""
                SELECT counter FROM fy_case_counters WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ?
                )
            """, (fy_end_year - 1,))
            counter_result = cursor.fetchone()
            db_counter = counter_result[0] if counter_result else None
            print(f"DEBUG: assign_case_numbers - db_counter: {db_counter}")

            # Check if there are cases from other financial years that might be interfering
            cursor.execute("""
                SELECT fy_id, COUNT(*), MAX(transaction_no)
                FROM cases
                WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?
                )
            """, (fy_end_year - 1, fy_end_year))
            fy_cases = cursor.fetchall()
            print(f"DEBUG: Cases for current FY {fy}: {fy_cases}")

            # Check all cases in database for this FY
            cursor.execute("""
                SELECT COUNT(*), MAX(transaction_no), MIN(transaction_no)
                FROM cases
                WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?
                )
            """, (fy_end_year - 1, fy_end_year))
            all_cases = cursor.fetchone()
            print(f"DEBUG: All cases for FY {fy}: count={all_cases[0]}, max={all_cases[1]}, min={all_cases[2]}")

            conn.close()

            # Filter out transactions marked for removal before assigning case numbers
            transactions_to_assign = [t for t in self.dialog.transactions if not t.get('marked_for_removal', False)]

            # Assign preview case numbers (don't increment database counter yet)
            for i, transaction in enumerate(transactions_to_assign):
                preview_number = current_counter + i + 1
                case_number = f"{fy_end_year}{preview_number:05d}"
                transaction['case_number'] = case_number

            # Store the next counter value for when import actually happens
            self.dialog.next_counter_value = current_counter + len(transactions_to_assign)

            # Update the table to show case numbers
            self.dialog.populate_transactions_table()

            # Keep import button enabled and disable assign button
            self.dialog.import_button.setEnabled(True)
            self.dialog.assign_case_numbers_button.setEnabled(False)
            self.dialog.assign_case_numbers_button.setText("Case Numbers Assigned")

            # Show what case numbers were assigned
            assigned_numbers = [t.get('case_number', 'No number') for t in transactions_to_assign[:5]]
            print(f"DEBUG: First 5 assigned case numbers: {assigned_numbers}")
            print(f"DEBUG: Total transactions to assign: {len(transactions_to_assign)}")
            print(f"DEBUG: ===== ASSIGN CASE NUMBERS END =====")

            QMessageBox.information(
                self.dialog, "Case Numbers Assigned",
                f"✅ Case numbers have been assigned to {len(transactions_to_assign)} transactions "
                f"(out of {len(self.dialog.transactions)} total).\n\n"
                f"Next available case number: {fy_end_year}{(current_counter + len(transactions_to_assign) + 1):05d}\n\n"
                "You can now proceed with importing the cases."
            )

        except Exception as e:
            QMessageBox.critical(self.dialog, "Error", f"Failed to assign case numbers:\n{str(e)}")

    def check_duplicates(self):
        """Check for duplicate cases based on responsibility matching"""
        if not self.dialog.transactions:
            QMessageBox.warning(self.dialog, "No Transactions", "No transactions to check for duplicates")
            return

        # Show progress
        self.dialog.progress_bar.setVisible(True)
        self.dialog.progress_bar.setValue(0)
        self.dialog.results_label.setText("Checking for duplicates...")

        total_transactions = len(self.dialog.transactions)
        duplicate_count = 0
        no_duplicate_count = 0

        # Initialize duplicate check results
        self.duplicate_check_results = []

        for i, transaction in enumerate(self.dialog.transactions):
            self.dialog.progress_bar.setValue(int((i / total_transactions) * 100))
            self.dialog.results_label.setText(f"Checking transaction {i+1} of {total_transactions}...")

            # Find duplicates for this transaction
            duplicates = find_duplicates(transaction, self.dialog.category)

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

        self.dialog.progress_bar.setVisible(False)

        # Update table to refresh Dup Status column
        self.dialog.populate_transactions_table()

        # Show summary
        self.dialog.results_label.setText(f"Duplicate check complete: {duplicate_count} with duplicates, {no_duplicate_count} without duplicates")

        QMessageBox.information(
            self.dialog, "Duplicate Check Complete",
            f"✅ Duplicate check completed.\n\n"
            f"Transactions with potential duplicates: {duplicate_count}\n"
            f"Transactions without duplicates: {no_duplicate_count}\n\n"
            f"Check the 'Dup Status' column for details.\n"
            f"Rows with duplicates are highlighted in the table."
        )

        # Enable next steps
        self.dialog.assign_case_numbers_button.setEnabled(True)
        self.dialog.import_button.setEnabled(False)  # Will be enabled after case numbers are assigned

    def import_cases(self):
        if not self.dialog.transactions:
            QMessageBox.warning(self.dialog, "No Transactions", "No transactions to import")
            return

        # Filter out transactions marked for removal before checking case numbers
        transactions_to_import = [t for t in self.dialog.transactions if not t.get('marked_for_removal', False)]

        if not transactions_to_import:
            QMessageBox.warning(self.dialog, "No Transactions", "All transactions have been marked for removal. Nothing to import.")
            return

        # FINANCIAL YEAR VALIDATION AND SELECTION
        # Check if the current financial year exists before proceeding with import
        current_fy = get_financial_year()
        fy_validation = validate_financial_year(current_fy)

        # Initialize selected_fy to None (will remain None if current FY is valid)
        self.dialog.selected_fy = None
        if not fy_validation['exists']:
            print(f"DEBUG: Current FY {current_fy} does not exist in database")
            print(f"DEBUG: FY validation result: {fy_validation}")

            # Show FY selection dialog
            from ..ui.dialogs.financial_year_selection_dialog import show_fy_selection_dialog
            selected_fy_data = show_fy_selection_dialog(current_fy, self.dialog)
            if selected_fy_data:
                self.dialog.selected_fy = selected_fy_data['fy_string']
                print(f"DEBUG: User selected FY: {self.dialog.selected_fy}")
                QMessageBox.information(
                    self.dialog, "Financial Year Selected",
                    f"✅ Import will use the selected financial year: {self.dialog.selected_fy}\n\n"
                    f"This ensures all cases are properly associated with an existing financial year."
                )
            else:
                QMessageBox.warning(
                    self.dialog, "Import Cancelled",
                    "❌ Import cancelled. You must select a valid financial year to proceed."
                )
                return
        else:
            print(f"DEBUG: Current FY {current_fy} exists and is valid")
            self.dialog.selected_fy = None  # Explicitly set to None for clarity

        # Check if case numbers have been assigned to transactions that will actually be imported
        transactions_without_case_numbers = [t for t in transactions_to_import if not t.get('case_number')]
        if transactions_without_case_numbers:
            QMessageBox.warning(
                self.dialog, "Case Numbers Required",
                f"{len(transactions_without_case_numbers)} transactions do not have case numbers assigned.\n\n"
                "Please click 'Assign Case Numbers' before importing cases."
            )
            return

        # Check if the period is open
        period_status = check_period_status(self.dialog.date_from, self.dialog.date_to)
        if period_status['status'] == 'closed':
            # Get current open period
            current_period = get_current_open_period()

            if current_period:
                # Parse string dates back to datetime objects for formatting
                start_date = datetime.strptime(current_period['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(current_period['end_date'], '%Y-%m-%d').date()

                reply = QMessageBox.question(
                    self.dialog, "Closed Period - Action Required",
                    f"CRITICAL: The selected date range ({self.dialog.date_from.strftime('%d/%m/%Y')} to {self.dialog.date_to.strftime('%d/%m/%Y')}) falls within a CLOSED period.\n\n"
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
                    self.dialog.date_from = current_period['start_date']
                    self.dialog.date_to = current_period['end_date']
                    QMessageBox.information(
                        self.dialog, "Period Changed",
                        f"✅ Import dates changed to current open period:\n"
                        f"From: {self.dialog.date_from.strftime('%d/%m/%Y')}\n"
                        f"To: {self.dialog.date_to.strftime('%d/%m/%Y')}\n\n"
                        f"This ensures compliance and data integrity."
                    )
                else:
                    QMessageBox.warning(
                        self.dialog, "Import Cancelled",
                        "❌ Import cancelled to prevent posting to closed period.\n\n"
                        "Please open the appropriate period first or select dates within an open period."
                    )
                    return
            else:
                QMessageBox.critical(
                    self.dialog, "No Open Period Available",
                    "❌ CRITICAL: The selected dates fall within a closed period AND no open period is available.\n\n"
                    "Please open a period in Financial Year Management before importing transactions.\n\n"
                    "⚠️  Transactions cannot be posted to closed periods."
                )
                return

        elif period_status['status'] == 'not_found':
            QMessageBox.warning(
                self.dialog, "Period Not Found",
                f"⚠️  Warning: Could not determine period status for the selected date range.\n\n"
                f"Date Range: {self.dialog.date_from.strftime('%d/%m/%Y')} to {self.dialog.date_to.strftime('%d/%m/%Y')}\n\n"
                "Please verify the dates are within a valid financial period."
            )
            return

        reply = QMessageBox.question(
            self.dialog, "Confirm Import",
            f"Import {len(transactions_to_import)} transactions as cases?\n\n"
            f"Date Range: {self.dialog.date_from.strftime('%d/%m/%Y')} to {self.dialog.date_to.strftime('%d/%m/%Y')}\n"
            "This will create new cases in the system.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.perform_import()

    def analyze_database_vs_import_data(self):
        """Comprehensive analysis of database content vs import data"""
        analyze_database_vs_import_data(self.dialog.transactions, self.dialog.category, self.dialog.date_from, self.dialog.date_to)