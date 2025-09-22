import sqlite3

from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_current_open_financial_year


def assign_case_numbers(dialog):
    """Assign case numbers to all transactions"""
    if not dialog.transactions:
        QMessageBox.warning(
            dialog, "No Transactions", "No transactions to assign case numbers to"
        )
        return

    try:
        # Clear any test data to avoid sequence skew
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete cases that appear to be test data (containing 'test' in description or transaction_no)
        cursor.execute(
            """
            DELETE FROM cases
            WHERE LOWER(description) LIKE '%test%' OR LOWER(transaction_no) LIKE '%test%'
        """
        )
        deleted_count = cursor.rowcount
        if deleted_count > 0:
            print(f"DEBUG: Cleared {deleted_count} test cases to reset numbering")

        conn.commit()

        # Get financial year
        fy = get_current_open_financial_year()
        fy_year = fy[1].split('-')[1] if fy else '26'

        # Get the highest existing transaction_no
        cursor.execute(
            """
            SELECT MAX(CAST(SUBSTR(transaction_no, -5) AS INTEGER))
            FROM cases
            WHERE transaction_no LIKE ?
            AND transaction_no IS NOT NULL
        """,
            (f"{fy_year}%",),
        )

        max_id = cursor.fetchone()[0]
        current_counter = max_id or 0
        conn.close()

        # Filter out transactions marked for removal before assigning case numbers
        transactions_to_assign = [
            t for t in dialog.transactions if not t.get("marked_for_removal", False)
        ]

        # Assign preview case numbers (don't increment database counter yet)
        for i, transaction in enumerate(transactions_to_assign):
            preview_number = current_counter + i + 1
            case_number = f"{fy_year}{preview_number:05d}"
            transaction["case_number"] = case_number
            # Also store base_transaction_no for the import worker
            transaction["base_transaction_no"] = case_number

        # Store the next counter value for when import actually happens
        dialog.next_counter_value = current_counter + len(transactions_to_assign)

        # Update the table to show case numbers
        from ..ui.components.import_cases_ui import populate_transactions_table

        populate_transactions_table(dialog)

        # Keep import button enabled and disable assign button
        dialog.import_button.setEnabled(True)
        dialog.assign_case_numbers_button.setEnabled(False)
        dialog.assign_case_numbers_button.setText("Case Numbers Assigned")

        QMessageBox.information(
            dialog,
            "Case Numbers Assigned",
            f"✅ Case numbers have been assigned to {len(transactions_to_assign)} transactions "
            f"(out of {len(dialog.transactions)} total).\n\n"
            f"Next available case number: {fy_year}{(current_counter + len(transactions_to_assign) + 1):05d}\n\n"
            "You can now proceed with importing the cases.",
        )

    except Exception as e:
        QMessageBox.critical(
            dialog, "Error", f"Failed to assign case numbers:\n{str(e)}"
        )
