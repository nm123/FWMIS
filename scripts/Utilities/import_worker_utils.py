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
    """Perform the actual import using the worker thread"""
    # Filter out transactions marked for removal (already done in import_cases, but being safe)
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

    print(
        f"DEBUG: Starting import with {len(transactions_to_import)} transactions (filtered from {len(dialog.transactions)})"
    )

    dialog.progress_bar.setVisible(True)
    dialog.progress_bar.setValue(0)
    dialog.import_button.setEnabled(False)

    dialog.worker = ImportWorker(
        transactions_to_import,
        dialog.category,
        dialog.date_from,
        dialog.date_to,
        dialog.bas_file_path,
    )
    dialog.worker.progress.connect(lambda p, m: update_progress(dialog, p, m))
    dialog.worker.finished.connect(lambda ic: import_finished(dialog, ic))
    dialog.worker.error.connect(lambda em: import_error(dialog, em))
    dialog.worker.start()


def update_progress(dialog, percentage, message):
    from ..ui.components.import_cases_ui import update_progress

    update_progress(dialog, percentage, message)


def import_finished(dialog, imported_cases):
    from ..ui.components.import_cases_ui import import_finished

    import_finished(dialog, imported_cases)


def import_error(dialog, error_msg):
    from ..ui.components.import_cases_ui import import_error

    import_error(dialog, error_msg)
