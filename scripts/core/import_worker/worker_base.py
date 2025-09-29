"""
Worker Base Module for Import Operations

Contains the base ImportWorker class with common functionality.
"""

import logging
from typing import List

from PyQt5.QtCore import QThread, pyqtSignal


class ImportWorker(QThread):
    """
    Worker thread for importing cases.

    Signals:
        progress: Emitted for progress updates (percentage, message)
        finished: Emitted when import completes (list of imported case numbers)
        error: Emitted when an error occurs (error message)
    """

    progress = pyqtSignal(int, str)  # progress percentage, current operation
    finished = pyqtSignal(list)  # list of imported case numbers
    error = pyqtSignal(str)

    def __init__(
        self,
        transactions: List[dict],
        category: dict,
        date_from: str,
        date_to: str,
        bas_file_path: str,
        selected_fy=None,
    ):
        """
        Initialize the import worker.

        Args:
            transactions: List of transaction dictionaries to import
            category: Category dictionary for the cases
            date_from: Start date for filtering
            date_to: End date for filtering
            bas_file_path: Path to BAS file for copying
            selected_fy: Optional financial year override
        """
        super().__init__()
        self.transactions = transactions
        self.category = category
        self.date_from = date_from
        self.date_to = date_to
        self.bas_file_path = bas_file_path
        self.selected_fy = selected_fy  # Optional: override the auto-determined FY
        self._cancelled = False

    def cancel(self) -> None:
        """Request cooperative cancellation of the worker."""
        self._cancelled = True

    def run(self) -> None:
        """
        Main import execution method.
        """
        try:
            # PRE-IMPORT DATABASE INTEGRITY CHECK
            self._check_database_integrity()

            imported_cases = []
            total = len(self.transactions)
            logging.getLogger(__name__).info(
                "ImportWorker starting", extra={"transaction_count": total}
            )

            for i, transaction in enumerate(self.transactions):
                if self._cancelled:
                    logging.getLogger(__name__).info("Import cancelled by user")
                    break

                try:
                    self.progress.emit(
                        int((i / total) * 100), f"Importing case {i+1} of {total}..."
                    )
                    logging.getLogger(__name__).debug(
                        "Processing transaction",
                        extra={
                            "index": i + 1,
                            "of": total,
                            "case_number": transaction.get("case_number", None),
                        },
                    )

                    # Import the transaction as a case
                    case_number = self._import_transaction(transaction)
                    if case_number:
                        imported_cases.append(case_number)
                        logging.getLogger(__name__).info(
                            "Imported case", extra={"case_number": case_number}
                        )
                    else:
                        logging.getLogger(__name__).warning(
                            "Failed to import transaction",
                            extra={"index": i + 1, "of": total},
                        )
                        # Continue with other transactions even if one fails
                        continue

                except Exception:
                    logging.getLogger(__name__).exception(
                        "Error importing transaction",
                        extra={"index": i + 1, "of": total},
                    )
                    # Continue with other transactions
                    continue

            logging.getLogger(__name__).info(
                "Import completed",
                extra={
                    "imported_count": len(imported_cases),
                    "cancelled": self._cancelled,
                },
            )
            self.progress.emit(100, "Import completed successfully")
            self.finished.emit(imported_cases)

        except Exception as e:
            logging.getLogger(__name__).exception("Import failed")
            self.error.emit(str(e))

    def _check_database_integrity(self) -> None:
        """
        Check database integrity before import.
        """
        # This will be implemented in the database_checks module
        pass

    def _import_transaction(self, transaction: dict) -> str:
        """
        Import a single transaction as a case.

        Args:
            transaction: Transaction dictionary to import

        Returns:
            str: Generated case number if successful, empty string otherwise
        """
        # This will be implemented in the transaction_processor module
        return ""
