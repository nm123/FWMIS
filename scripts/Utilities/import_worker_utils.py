from PyQt5.QtWidgets import QMessageBox
from scripts.core.import_worker import ImportWorker


def import_cases(dialog):
    """Import cases using the worker thread"""
    if not dialog.transactions:
        QMessageBox.warning(dialog, "No Transactions", "No transactions to import")
        return

    # Filter out transactions marked for removal before checking case numbers
    transactions_to_import = [
        t for t in dialog.transactions if not t.get("marked_for_removal", False)
    ]

    if not transactions_to_import:
        QMessageBox.warning(
            dialog,
            "No Transactions",
            "All transactions have been marked for removal. Nothing to import.",
        )
        return

    # Check if case numbers have been assigned to transactions that will actually be imported
    transactions_without_case_numbers = [
        t for t in transactions_to_import if not t.get("case_number")
    ]
    if transactions_without_case_numbers:
        QMessageBox.warning(
            dialog,
            "Case Numbers Required",
            f"{len(transactions_without_case_numbers)} transactions do not have case numbers assigned.\n\n"
            "Please click 'Assign Case Numbers' before importing cases.",
        )
        return

    reply = QMessageBox.question(
        dialog,
        "Confirm Import",
        f"Import {len(transactions_to_import)} transactions as cases?\n\n"
        f"Date Range: {dialog.date_from.strftime('%d/%m/%Y')} to {dialog.date_to.strftime('%d/%m/%Y')}\n"
        "This will create new cases in the system.",
        QMessageBox.Yes | QMessageBox.No,
    )

    if reply == QMessageBox.Yes:
        perform_import(dialog)


def perform_import(dialog):
    """Perform the actual import synchronously"""
    transactions_to_import = [
        t for t in dialog.transactions if not t.get("marked_for_removal", False)
    ]

    if not transactions_to_import:
        QMessageBox.warning(
            dialog,
            "No Transactions",
            "All transactions have been marked for removal. Nothing to import.",
        )
        return

    dialog.cancelled = False
    imported_cases = []
    imported_ids = []
    total = len(transactions_to_import)

    dialog.progress_bar.setVisible(True)
    dialog.progress_bar.setValue(0)
    dialog.import_button.setEnabled(False)

    for i, transaction in enumerate(transactions_to_import):
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        if dialog.cancelled:
            break
        dialog.progress_bar.setValue(int((i / total) * 100))
        dialog.results_label.setText(f"Importing case {i+1} of {total}...")
        case_number, case_id = _import_transaction_sync(transaction, dialog.category, dialog.date_from, dialog.date_to, dialog.bas_file_path)
        if case_number:
            imported_cases.append(case_number)
            imported_ids.append(case_id)

    dialog.progress_bar.setVisible(False)

    if dialog.cancelled:
        if imported_ids:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(imported_ids))
            cursor.execute(f"DELETE FROM cases WHERE id IN ({placeholders})", imported_ids)
            conn.commit()
            conn.close()
        QMessageBox.information(dialog, "Import Cancelled", "Import was cancelled. Imported cases have been deleted.")
        dialog.reject()
    else:
        QMessageBox.information(
            dialog,
            "Import Complete",
            f"Successfully imported {len(imported_cases)} cases:\n\n"
            + "\n".join(imported_cases[:10])
            + (
                f"\n... and {len(imported_cases) - 10} more"
                if len(imported_cases) > 10
                else ""
            ),
        )
        dialog.accept()


def update_progress(dialog, percentage, message):
    from ..ui.components.import_cases_ui import update_progress

    update_progress(dialog, percentage, message)


def import_finished(dialog, imported_cases):
    from ..ui.components.import_cases_ui import import_finished

    import_finished(dialog, imported_cases)


def import_error(dialog, error_msg):
    from ..ui.components.import_cases_ui import import_error

    import_error(dialog, error_msg)
