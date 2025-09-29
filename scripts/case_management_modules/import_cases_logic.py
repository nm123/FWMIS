from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.import_assignment_utils import assign_case_numbers
from scripts.Utilities.import_duplicate_utils import find_duplicates
from scripts.Utilities.import_parsing_utils import parse_bas_file
from scripts.Utilities.import_validation_utils import validate_imported_cases
from scripts.Utilities.import_worker_utils import (
    import_cases,
    import_error,
    import_finished,
    perform_import,
    update_progress,
)


class ImportCasesLogic:
    def __init__(self, dialog):
        self.dialog = dialog

    def parse_file(self):
        if not self.dialog.bas_file_path or not self.dialog.category:
            return

        try:
            # Parse BAS file and extract dates
            transactions, extracted_date_from, extracted_date_to = parse_bas_file(
                self.dialog.bas_file_path
            )

            # If dates were extracted from header, use them
            if extracted_date_from and extracted_date_to:
                self.dialog.date_from_edit.setDate(QDate(extracted_date_from))
                self.dialog.date_to_edit.setDate(QDate(extracted_date_to))
                QMessageBox.information(
                    self.dialog,
                    "Dates Extracted",
                    f"Dates automatically extracted from report header:\n"
                    f"From: {extracted_date_from.strftime('%d/%m/%Y')}\n"
                    f"To: {extracted_date_to.strftime('%d/%m/%Y')}\n\n"
                    f"You can modify these dates if needed.",
                )

            self.dialog.date_from = self.dialog.date_from_edit.date().toPyDate()
            self.dialog.date_to = self.dialog.date_to_edit.date().toPyDate()

            # Validate imported cases
            transactions = validate_imported_cases(transactions)

            self.dialog.transactions = transactions

            # Get summary (similar to BASParser.get_transaction_summary)
            total_count = len(transactions)
            debit_count = len([t for t in transactions if not t["is_credit"]])
            credit_count = len([t for t in transactions if t["is_credit"]])
            total_amount = sum(abs(t["amount"]) for t in transactions)
            try:
                from scripts.Utilities.utils import format_currency_amount

                summary = f"Found {total_count} transactions ({debit_count} debits, {credit_count} credits) totaling {format_currency_amount(total_amount)}"
            except ImportError:
                summary = f"Found {total_count} transactions ({debit_count} debits, {credit_count} credits) totaling R{total_amount:,.2f}"

            self.dialog.results_label.setText(summary)
            from scripts.ui.components.import_cases_ui import populate_transactions_table

            populate_transactions_table(self.dialog)

            # Enable next steps
            self.dialog.manage_resp_button.setEnabled(True)
            self.dialog.check_duplicates_button.setEnabled(True)
            # Note: Import button will be enabled after duplicate check or case number assignment

        except Exception as e:
            QMessageBox.critical(
                self.dialog, "Parse Error", f"Failed to parse BAS file:\n{str(e)}"
            )

    def check_duplicates(self):
        """Check for duplicate cases based on responsibility matching"""
        if not self.dialog.transactions:
            QMessageBox.warning(
                self.dialog,
                "No Transactions",
                "No transactions to check for duplicates",
            )
            return

        # Show progress
        self.dialog.progress_bar.setVisible(True)
        self.dialog.progress_bar.setValue(0)
        self.dialog.results_label.setText("Checking for duplicates...")

        total_transactions = len(self.dialog.transactions)
        duplicate_count = 0
        no_duplicate_count = 0

        # Initialize duplicate check results
        self.dialog.duplicate_check_results = []

        for i, transaction in enumerate(self.dialog.transactions):
            self.dialog.progress_bar.setValue(int((i / total_transactions) * 100))
            self.dialog.results_label.setText(
                f"Checking transaction {i+1} of {total_transactions}..."
            )

            # Find duplicates for this transaction
            duplicates = find_duplicates(transaction, self.dialog.category["name"])

            # Store result for table display
            result = {
                "transaction_index": i,
                "duplicates": duplicates,
                "duplicate_count": len(duplicates),
            }
            self.dialog.duplicate_check_results.append(result)

            if duplicates:
                duplicate_count += 1
            else:
                no_duplicate_count += 1

        self.dialog.progress_bar.setVisible(False)

        # Update table to refresh Dup Status column
        from ..ui.components.import_cases_ui import populate_transactions_table

        populate_transactions_table(self.dialog)

        # Show summary
        self.dialog.results_label.setText(
            f"Duplicate check complete: {duplicate_count} with duplicates, {no_duplicate_count} without duplicates"
        )

        QMessageBox.information(
            self.dialog,
            "Duplicate Check Complete",
            f"✅ Duplicate check completed.\n\n"
            f"Transactions with potential duplicates: {duplicate_count}\n"
            f"Transactions without duplicates: {no_duplicate_count}\n\n"
            f"Check the 'Dup Status' column for details.\n"
            f"Rows with duplicates are highlighted in the table.",
        )

        # Enable next steps
        self.dialog.assign_case_numbers_button.setEnabled(True)
        self.dialog.import_button.setEnabled(
            False
        )  # Will be enabled after case numbers are assigned

    def assign_case_numbers(self):
        assign_case_numbers(self.dialog)

    def import_cases(self):
        import_cases(self.dialog)

    def perform_import(self):
        perform_import(self.dialog)

    def update_progress(self, percentage, message):
        update_progress(self.dialog, percentage, message)

    def import_finished(self, imported_cases):
        import_finished(self.dialog, imported_cases)

    def import_error(self, error_msg):
        import_error(self.dialog, error_msg)
