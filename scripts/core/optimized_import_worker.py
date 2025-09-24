"""
Optimized Import Worker with memory-efficient components.
Integrates streaming processing, batch operations, and performance monitoring.
"""

import os
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any

from PyQt5.QtCore import QThread, pyqtSignal
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.db_utils import get_db_connection
from scripts.Utilities.financial_utils import (create_year_folder,
                                               generate_transaction_no,
                                               get_financial_year)
from scripts.Utilities.responsibility_utils import load_posting_responsibilities
from scripts.Utilities.optimized_import_utils import (
    OptimizedBASParser, BatchDatabaseInserter, memory_efficient_db_connection,
    create_performance_indexes, optimize_database_settings, memory_usage_monitor
)
# Import performance profiler conditionally to avoid circular imports
try:
    from scripts.Utilities.performance_profiler import performance_profiler, memory_profiler
except ImportError:
    # Fallback if performance profiler is not available
    class DummyProfiler:
        def take_snapshot(self, label): pass
        def timer(self, name): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    performance_profiler = DummyProfiler()
    memory_profiler = DummyProfiler()

logger = logging.getLogger(__name__)


class OptimizedImportWorker(QThread):
    """Memory-efficient worker thread for importing cases with streaming and batch processing"""

    progress = pyqtSignal(int, str)  # progress percentage, current operation
    finished = pyqtSignal(list)  # list of imported case numbers
    error = pyqtSignal(str)

    def __init__(
        self,
        transactions,
        category,
        date_from,
        date_to,
        bas_file_path,
        selected_fy=None,
        use_streaming=True,
        batch_size=None
    ):
        super().__init__()
        self.transactions = transactions
        self.category = category
        self.date_from = date_from
        self.date_to = date_to
        self.bas_file_path = bas_file_path
        self.selected_fy = selected_fy
        self.use_streaming = use_streaming
        self.batch_size = batch_size
        self._cancelled = False
        
        # Initialize optimized components
        self.batch_inserter = BatchDatabaseInserter(batch_size)
        self.parser = OptimizedBASParser()

    def cancel(self):
        """Request cooperative cancellation of the worker."""
        self._cancelled = True

    def run(self):
        """Main import process with memory optimization and performance monitoring."""
        try:
            # Start performance monitoring
            memory_profiler.take_snapshot("import_start")
            with performance_profiler.timer("total_import"):
                
                # Apply database optimizations
                self._apply_database_optimizations()
                
                # Check memory before starting
                if not memory_usage_monitor():
                    self.error.emit("Insufficient memory for import operation")
                    return
                
                # PRE-IMPORT DATABASE INTEGRITY CHECK
                self._check_database_integrity()

                imported_cases = []
                total = len(self.transactions)
                
                logger.info("OptimizedImportWorker starting", 
                           extra={"transaction_count": total, "use_streaming": self.use_streaming})

                if self.use_streaming and total > 1000:
                    # Use streaming processing for large datasets
                    imported_cases = self._process_streaming_import()
                else:
                    # Use batch processing for smaller datasets
                    imported_cases = self._process_batch_import()

                logger.info("Import completed", 
                           extra={"imported_count": len(imported_cases), "cancelled": self._cancelled})
                
                # Final memory snapshot
                memory_profiler.take_snapshot("import_complete")
                
                self.progress.emit(100, "Import completed successfully")
                self.finished.emit(imported_cases)

        except Exception as e:
            logger.exception("OptimizedImportWorker critical error")
            self.error.emit(f"Critical import error: {str(e)}")

    def _apply_database_optimizations(self):
        """Apply database optimizations for better performance."""
        try:
            optimize_database_settings()
            create_performance_indexes()
            logger.info("Database optimizations applied successfully")
        except Exception as e:
            logger.warning(f"Failed to apply some database optimizations: {e}")

    def _check_database_integrity(self):
        """Check for database integrity issues before importing."""
        try:
            with memory_efficient_db_connection() as conn:
                cursor = conn.cursor()

                # Check for cases with invalid fy_id
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases c
                    LEFT JOIN financial_years fy ON c.fy_id = fy.id
                    WHERE c.list != 'Deleted Cases' AND fy.id IS NULL
                """
                )
                orphaned_count = cursor.fetchone()[0]

                if orphaned_count > 0:
                    logger.warning("Database integrity: cases with invalid fy_id",
                                 extra={"count": orphaned_count})

                # Check for current FY availability
                fy = self.selected_fy or get_financial_year()
                fy_parts = fy.split("-")
                start_year = int(fy_parts[0])
                end_year = int(fy_parts[1])

                cursor.execute(
                    "SELECT COUNT(*) FROM financial_years WHERE start_year = ? AND end_year = ?",
                    (start_year, end_year),
                )
                fy_count = cursor.fetchone()[0]

                if fy_count == 0:
                    logger.error("Current FY not found in database", extra={"fy": fy})
                    raise Exception(f"Financial Year {fy} not found in database")

        except Exception as e:
            logger.exception("Database integrity check failed")
            raise

    def _process_streaming_import(self) -> List[str]:
        """Process import using streaming for memory efficiency."""
        imported_cases = []
        total = len(self.transactions)
        
        logger.info("Starting streaming import process")
        
        # Process transactions in chunks
        chunk_size = self.batch_size or 1000
        for i in range(0, total, chunk_size):
            if self._cancelled:
                logger.info("Streaming import cancelled by user")
                break
                
            chunk = self.transactions[i:i + chunk_size]
            chunk_imported = self._process_chunk(chunk, i + 1, total)
            imported_cases.extend(chunk_imported)
            
            # Update progress
            progress = int(((i + len(chunk)) / total) * 100)
            self.progress.emit(progress, f"Processed {i + len(chunk)} of {total} transactions...")
            
            # Monitor memory usage
            if not memory_usage_monitor():
                logger.warning("High memory usage detected, reducing chunk size")
                chunk_size = max(chunk_size // 2, 100)  # Reduce chunk size
        
        return imported_cases

    def _process_batch_import(self) -> List[str]:
        """Process import using batch operations."""
        imported_cases = []
        total = len(self.transactions)
        
        logger.info("Starting batch import process")
        
        # Prepare cases for batch insertion
        cases_to_insert = []
        
        for i, transaction in enumerate(self.transactions):
            if self._cancelled:
                logger.info("Batch import cancelled by user")
                break
                
            try:
                self.progress.emit(
                    int((i / total) * 100), f"Preparing case {i+1} of {total}..."
                )
                
                # Prepare case data
                case_data = self._prepare_case_data(transaction)
                if case_data:
                    cases_to_insert.append(case_data)
                    
            except Exception as e:
                logger.exception("Error preparing transaction", 
                               extra={"index": i + 1, "of": total})
                continue
        
        # Batch insert all cases
        if cases_to_insert:
            logger.info(f"Batch inserting {len(cases_to_insert)} cases")
            self.progress.emit(90, f"Inserting {len(cases_to_insert)} cases...")
            
            fy_id = self._get_fy_id()
            inserted_case_numbers = self.batch_inserter.insert_cases_batch(cases_to_insert, fy_id)
            imported_cases.extend(inserted_case_numbers)
            
            # Copy BAS files for all cases
            self._copy_bas_files_batch(imported_cases)
        
        return imported_cases

    def _process_chunk(self, chunk: List[Dict], start_index: int, total: int) -> List[str]:
        """Process a chunk of transactions."""
        imported_cases = []
        
        for i, transaction in enumerate(chunk):
            if self._cancelled:
                break
                
            try:
                case_number = self._import_transaction_optimized(transaction)
                if case_number:
                    imported_cases.append(case_number)
                    logger.info("Imported case", extra={"case_number": case_number})
                    
            except Exception as e:
                logger.exception("Error importing transaction", 
                               extra={"index": start_index + i, "of": total})
                continue
        
        return imported_cases

    def _prepare_case_data(self, transaction: Dict) -> Dict:
        """Prepare case data for batch insertion."""
        try:
            fy_id = self._get_fy_id()
            period_id = self._get_period_id(transaction["date"], fy_id)
            resp_id = self._get_responsibility_id(transaction["responsibility"])
            
            if not fy_id or not resp_id:
                return None
            
            # Use the case number that was already assigned during preview
            case_number = transaction.get("case_number")
            base_transaction_no = transaction.get("base_transaction_no", case_number)
            
            if not case_number:
                case_number = self._generate_case_number(fy_id)
                base_transaction_no = case_number
            
            # Prepare case data
            date_str = transaction["date"].strftime("%Y-%m-%d")
            
            # Determine list and status based on transaction type
            if transaction["type"] == "GJ":
                list_name = "Checklist"
                status = "Alleged"
                description = f"{transaction['item']}. Journal authorised by BAS user {transaction['user_id']}"
                bas_journal_no = transaction["number"].lstrip("0") or "0"
                bas_journal_date = date_str
                bas_payment_no = None
                bas_payment_date = None
            elif transaction["type"] == "AP":
                list_name = "Checklist"
                status = "Alleged"
                description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                bas_journal_no = None
                bas_journal_date = None
                bas_payment_no = transaction["number"].lstrip("0") or "0"
                bas_payment_date = date_str
            else:  # CL
                list_name = "Checklist"
                status = "Alleged"
                description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                bas_journal_no = None
                bas_journal_date = None
                bas_payment_no = transaction["number"].lstrip("0") or "0"
                bas_payment_date = date_str
            
            return {
                "transaction_no": case_number,
                "base_transaction_no": base_transaction_no,
                "date_incurred": date_str,
                "date_identified": date_str,
                "date_reported": date_str,
                "description": description,
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": bas_payment_date,
                "persal_no": None,
                "category": self.category["name"],
                "responsibility_id": resp_id,
                "amount": abs(transaction["amount"]),
                "source_document": None,
                "minutes": None,
                "evidence_path": None,
                "status": status,
                "list": list_name,
                "assessment_assessed_by": None,
                "assessment_date": None,
                "assessment_result": None,
                "period_id": period_id,
                "criminal_charges": "N/A",
                "disciplinary_process": "N/A",
                "loss_recovery": "N/A",
                "prevention_steps": "N/A",
                "original_list": list_name,
                "attachments": "[]",
                "shared_document_id": None,
                "bas_journal_no": bas_journal_no,
                "bas_journal_date": bas_journal_date,
            }
            
        except Exception as e:
            logger.exception("Error preparing case data")
            return None

    def _import_transaction_optimized(self, transaction: Dict) -> str:
        """Import a single transaction with optimized database operations."""
        try:
            with memory_efficient_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get financial year ID
                fy_id = self._get_fy_id()
                if not fy_id:
                    raise Exception("Financial Year not found")
                
                # Get period and responsibility IDs
                period_id = self._get_period_id(transaction["date"], fy_id)
                resp_id = self._get_responsibility_id(transaction["responsibility"])
                
                if not resp_id:
                    raise Exception(f"Responsibility '{transaction['responsibility']}' not found")
                
                # Use the case number that was already assigned during preview
                case_number = transaction.get("case_number")
                base_transaction_no = transaction.get("base_transaction_no", case_number)
                
                if not case_number:
                    case_number = self._generate_case_number(fy_id)
                    base_transaction_no = case_number
                
                # Prepare case data
                date_str = transaction["date"].strftime("%Y-%m-%d")
                
                # Determine list and status based on transaction type
                if transaction["type"] == "GJ":
                    list_name = "Checklist"
                    status = "Alleged"
                    description = f"{transaction['item']}. Journal authorised by BAS user {transaction['user_id']}"
                    bas_journal_no = transaction["number"].lstrip("0") or "0"
                    bas_journal_date = date_str
                    bas_payment_no = None
                    bas_payment_date = None
                elif transaction["type"] == "AP":
                    list_name = "Checklist"
                    status = "Alleged"
                    description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                    bas_journal_no = None
                    bas_journal_date = None
                    bas_payment_no = transaction["number"].lstrip("0") or "0"
                    bas_payment_date = date_str
                else:  # CL
                    list_name = "Checklist"
                    status = "Alleged"
                    description = f"{transaction['description']} Payment authorised by BAS user {transaction['user_id']}"
                    bas_journal_no = None
                    bas_journal_date = None
                    bas_payment_no = transaction["number"].lstrip("0") or "0"
                    bas_payment_date = date_str
                
                # Insert case
                cursor.execute(
                    """
                    INSERT INTO cases (
                        transaction_no, base_transaction_no, date_incurred, date_identified, date_reported,
                        description, bas_payment_no, bas_payment_date, persal_no, category,
                        responsibility_id, amount, source_document, minutes, evidence_path,
                        status, list, assessment_assessed_by, assessment_date, assessment_result,
                        fy_id, period_id, criminal_charges, disciplinary_process, loss_recovery,
                        prevention_steps, original_list, attachments, shared_document_id, bas_journal_no, bas_journal_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        case_number, base_transaction_no, date_str, date_str, date_str,
                        description, bas_payment_no, bas_payment_date, None, self.category["name"],
                        resp_id, abs(transaction["amount"]), None, None, None,
                        status, list_name, None, None, None,
                        fy_id, period_id, "N/A", "N/A", "N/A",
                        "N/A", list_name, "[]", None, bas_journal_no, bas_journal_date,
                    ),
                )
                
                case_id = cursor.lastrowid
                logger.info("Case inserted", extra={"case_number": case_number, "id": case_id})
                
                # Create case-specific supporting evidence folder
                fy = self.selected_fy or get_financial_year()
                year_folder = create_year_folder(fy)
                supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
                case_folder = os.path.join(supporting_evidence_folder, f"Case {case_number}")
                os.makedirs(case_folder, exist_ok=True)
                
                # Copy BAS file if needed
                if self.bas_file_path:
                    self._copy_bas_file(case_number, transaction["date"], fy_id)
                
                # Log audit
                self._log_audit(transaction, case_number)
                
                return case_number
                
        except Exception as e:
            logger.exception("Error importing transaction")
            return None

    def _get_fy_id(self) -> int:
        """Get financial year ID."""
        fy = self.selected_fy or get_financial_year()
        fy_parts = fy.split("-")
        start_year = int(fy_parts[0])
        end_year = int(fy_parts[1])
        
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
                (start_year, end_year),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _get_period_id(self, date_obj, fy_id: int) -> int:
        """Get period ID for the given date and financial year."""
        date_str = date_obj.strftime("%Y-%m-%d")
        
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.id FROM periods p
                INNER JOIN financial_years fy ON p.fy_id = fy.id
                WHERE p.fy_id = ? AND p.start_date <= ? AND p.end_date >= ?
                ORDER BY p.period_number DESC LIMIT 1
            """,
                (fy_id, date_str, date_str),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _get_responsibility_id(self, responsibility_name: str) -> int:
        """Get responsibility ID by name."""
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM responsibilities WHERE name = ?",
                (responsibility_name,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _generate_case_number(self, fy_id: int) -> str:
        """Generate a new case number for the financial year."""
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MAX(CAST(SUBSTR(base_transaction_no, -5) AS INTEGER))
                FROM cases
                WHERE fy_id = ? AND fy_id IS NOT NULL AND base_transaction_no IS NOT NULL
                AND list != 'Deleted Cases'
            """,
                (fy_id,),
            )
            max_num = cursor.fetchone()[0]
            next_num = (max_num or 0) + 1
            
            fy = self.selected_fy or get_financial_year()
            fy_end_year = int(fy.split("-")[1])
            return f"FW-{fy_end_year}{next_num:05d}"

    def _copy_bas_file(self, case_number: str, date_obj, fy_id: int):
        """Copy BAS file to proper location."""
        try:
            fy = self.selected_fy or get_financial_year()
            year_folder = create_year_folder(fy)
            bas_files_folder = os.path.join(year_folder, "Imported BAS Files")
            
            month_str = date_obj.strftime("%Y%m")
            month_folder = os.path.join(bas_files_folder, month_str)
            
            os.makedirs(month_folder, exist_ok=True)
            
            original_filename = os.path.basename(self.bas_file_path)
            bas_file_path = os.path.join(month_folder, original_filename)
            
            shutil.copy2(self.bas_file_path, bas_file_path)
            
            # Update source_document field
            with memory_efficient_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cases SET source_document = ? WHERE transaction_no = ?",
                    (bas_file_path, case_number),
                )
            
            logger.info("Copied BAS file", extra={"path": bas_file_path})
            
        except Exception as e:
            logger.exception("Error copying BAS file")

    def _copy_bas_files_batch(self, case_numbers: List[str]):
        """Copy BAS files for multiple cases in batch."""
        if not self.bas_file_path or not case_numbers:
            return
            
        try:
            fy = self.selected_fy or get_financial_year()
            year_folder = create_year_folder(fy)
            bas_files_folder = os.path.join(year_folder, "Imported BAS Files")
            
            # Create a single copy for all cases in the same month
            # (assuming all transactions are from the same month)
            if case_numbers:
                # Get date from first transaction
                first_transaction = next((t for t in self.transactions if t.get("case_number") == case_numbers[0]), None)
                if first_transaction:
                    month_str = first_transaction["date"].strftime("%Y%m")
                    month_folder = os.path.join(bas_files_folder, month_str)
                    
                    os.makedirs(month_folder, exist_ok=True)
                    
                    original_filename = os.path.basename(self.bas_file_path)
                    bas_file_path = os.path.join(month_folder, original_filename)
                    
                    shutil.copy2(self.bas_file_path, bas_file_path)
                    
                    # Update source_document field for all cases
                    with memory_efficient_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE cases SET source_document = ? WHERE transaction_no IN ({})".format(
                                ",".join("?" * len(case_numbers))
                            ),
                            [bas_file_path] + case_numbers,
                        )
                    
                    logger.info("Copied BAS file for batch", extra={"path": bas_file_path, "cases": len(case_numbers)})
                    
        except Exception as e:
            logger.exception("Error copying BAS files in batch")

    def _log_audit(self, transaction: Dict, case_number: str):
        """Log audit information for the imported case."""
        try:
            def convert_dates(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates(item) for item in obj]
                elif hasattr(obj, "isoformat"):
                    return obj.isoformat()
                else:
                    return obj

            audit_transaction = convert_dates(transaction)
            fy = self.selected_fy or get_financial_year()
            
            save_audit_log(
                "import_undisclosed_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_number": case_number,
                    "transaction": audit_transaction,
                    "category": self.category["name"],
                },
                fy,
            )
        except Exception as e:
            logger.warning(f"Failed to save audit log: {e}")