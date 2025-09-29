"""
Import Worker Module

Main import worker class that combines all import functionality.
"""

from typing import List

from .database_checks import DatabaseIntegrityChecker
from .transaction_processor import TransactionProcessor
from .worker_base import ImportWorker as BaseImportWorker


class ImportWorker(BaseImportWorker):
    """
    Enhanced import worker that combines all import functionality.
    """

    def _check_database_integrity(self) -> None:
        """
        Check database integrity before import.
        """
        DatabaseIntegrityChecker.check_database_integrity(self)

    def _import_transaction(self, transaction: dict) -> str:
        """
        Import a single transaction as a case.

        Args:
            transaction: Transaction dictionary to import

        Returns:
            str: Generated case number if successful, empty string otherwise
        """
        return TransactionProcessor.import_transaction(self, transaction)
