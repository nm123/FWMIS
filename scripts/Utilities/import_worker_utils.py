from PyQt5.QtWidgets import QMessageBox
from scripts.core.import_worker import ImportWorker
from scripts.core.optimized_import_worker import OptimizedImportWorker
from scripts.Utilities.optimization_manager import get_optimization_manager


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
        # Use background worker (consistent with other import flow)
        dialog.progress_bar.setVisible(True)
        dialog.progress_bar.setValue(0)
        dialog.import_button.setEnabled(False)

        # Some dialogs may not set selected_fy; default to None
        selected_fy = getattr(dialog, "selected_fy", None)

        # Get optimization manager and auto-enable for large datasets
        optimization_manager = get_optimization_manager()
        data_size = len(transactions_to_import)
        
        # Auto-enable optimizations for large datasets
        optimizations_enabled = optimization_manager.auto_enable_for_large_dataset(data_size, "import")
        
        if optimizations_enabled:
            # Use optimized worker for large datasets
            use_streaming = optimization_manager.should_use_streaming(data_size)
            batch_size = optimization_manager.get_optimal_chunk_size()
            
            dialog.worker = OptimizedImportWorker(
                transactions_to_import,
                dialog.category,
                dialog.date_from,
                dialog.date_to,
                dialog.bas_file_path,
                selected_fy,
                use_streaming=use_streaming,
                batch_size=batch_size,
            )
            
            # Show optimization notification
            QMessageBox.information(
                dialog,
                "Performance Optimization",
                f"Large dataset detected ({data_size} cases).\n\n"
                "Performance optimizations have been automatically enabled:\n"
                "• Memory-efficient imports\n"
                "• Batch database operations\n"
                "• Adaptive chunk sizing\n\n"
                "This will provide better performance and memory usage."
            )
        else:
            # Use original worker for small datasets
            dialog.worker = ImportWorker(
                transactions_to_import,
                dialog.category,
                dialog.date_from,
                dialog.date_to,
                dialog.bas_file_path,
                selected_fy,
            )
        dialog.worker.progress.connect(lambda p, m: update_progress(dialog, p, m))
        dialog.worker.finished.connect(lambda cases: import_finished(dialog, cases))
        dialog.worker.error.connect(lambda msg: import_error(dialog, msg))
        dialog.worker.start()


def perform_import(dialog):
    """Deprecated synchronous import. Use import_cases() which starts the worker."""
    QMessageBox.information(
        dialog,
        "Import",
        "The import will now run in the background. Please monitor progress.",
    )
    import_cases(dialog)


def update_progress(dialog, percentage, message):
    from ..ui.components.import_cases_ui import update_progress

    update_progress(dialog, percentage, message)


def import_finished(dialog, imported_cases):
    from ..ui.components.import_cases_ui import import_finished

    import_finished(dialog, imported_cases)


def import_error(dialog, error_msg):
    from ..ui.components.import_cases_ui import import_error

    import_error(dialog, error_msg)
