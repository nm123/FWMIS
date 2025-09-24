import os
import shutil
import logging
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.db_utils import get_db_connection
from scripts.Utilities.financial_utils import (create_year_folder,
                                               generate_transaction_no,
                                               get_financial_year)
from scripts.Utilities.responsibility_utils import \
    load_posting_responsibilities


class ImportWorker(QThread):
    """Worker thread for importing cases"""

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
    ):
        super().__init__()
        self.transactions = transactions
        self.category = category
        self.date_from = date_from
        self.date_to = date_to
        self.bas_file_path = bas_file_path
        self.selected_fy = selected_fy  # Optional: override the auto-determined FY
        self._cancelled = False

    def cancel(self):
        """Request cooperative cancellation of the worker."""
        self._cancelled = True

    def run(self):
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
                extra={"imported_count": len(imported_cases), "cancelled": self._cancelled},
            )
            self.progress.emit(100, "Import completed successfully")
            self.finished.emit(imported_cases)

        except Exception as e:
            logging.getLogger(__name__).exception("ImportWorker critical error")
            self.error.emit(f"Critical import error: {str(e)}")

    def _check_database_integrity(self):
        """Check for database integrity issues before importing"""
        try:
            conn_ctx = get_db_connection()
            conn = conn_ctx.__enter__()
            try:
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
                    logging.getLogger(__name__).warning(
                        "Database integrity: cases with invalid fy_id",
                        extra={"count": orphaned_count},
                    )

                # Check for current FY availability
                fy = get_financial_year()
                fy_parts = fy.split("-")
                start_year = int(fy_parts[0])
                end_year = int(fy_parts[1])

                cursor.execute(
                    "SELECT COUNT(*) FROM financial_years WHERE start_year = ? AND end_year = ?",
                    (start_year, end_year),
                )
                fy_count = cursor.fetchone()[0]

                if fy_count == 0:
                    logging.getLogger(__name__).error(
                        "Current FY not found in database", extra={"fy": fy}
                    )
            finally:
                try:
                    conn_ctx.__exit__(None, None, None)
                except Exception:
                    pass

        except Exception:
            logging.getLogger(__name__).exception("Database integrity check failed")
            # Don't fail the import for integrity check failures

    def _import_transaction(self, transaction):
        """Import a single transaction as a case"""
        try:
            logging.getLogger(__name__).debug(
                "_import_transaction called",
                extra={"case_number": transaction.get("case_number", None)},
            )
            # Keep the connection open for the duration of this import to avoid using a closed cursor
            conn_ctx = get_db_connection()
            conn = conn_ctx.__enter__()
            try:
                cursor = conn.cursor()

                # Get financial year - use selected FY if provided, otherwise auto-determine
                if self.selected_fy:
                    fy = self.selected_fy
                    logging.getLogger(__name__).debug(
                        "Using selected FY", extra={"fy": fy}
                    )
                else:
                    fy = get_financial_year()
                    logging.getLogger(__name__).debug(
                        "Using auto-determined FY", extra={"fy": fy}
                    )

                fy_parts = fy.split("-")
                start_year = int(fy_parts[0])
                end_year = int(fy_parts[1])

                # Get financial year ID
                cursor.execute(
                    "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
                    (start_year, end_year),
                )
                fy_result = cursor.fetchone()
                fy_id = fy_result[0] if fy_result else None

                logging.getLogger(__name__).debug(
                    "FY resolved",
                    extra={
                        "fy": fy,
                        "start_year": start_year,
                        "end_year": end_year,
                        "fy_id": fy_id,
                    },
                )

                # Check what cases exist for this FY before import
                if fy_id:
                    cursor.execute(
                        "SELECT COUNT(*), MAX(transaction_no) FROM cases WHERE fy_id = ?",
                        (fy_id,),
                    )
                    existing_cases = cursor.fetchone()
                    logging.getLogger(__name__).debug(
                        "Existing cases in FY",
                        extra={
                            "fy": fy,
                            "fy_id": fy_id,
                            "count": existing_cases[0],
                            "max": existing_cases[1],
                        },
                    )

                # CRITICAL: Check if fy_id is valid before proceeding
                if fy_id is None:
                    logging.getLogger(__name__).error(
                        "FY not found in database", extra={"fy": fy}
                    )
                    raise Exception(
                        f"Financial Year {fy} not found in database. Please ensure the financial year is properly set up in Financial Year Management before importing cases."
                    )

                # ADDITIONAL SAFETY CHECK: Verify fy_id actually exists and is valid
                cursor.execute(
                    "SELECT id, start_year, end_year, status FROM financial_years WHERE id = ?",
                    (fy_id,),
                )
                verify_result = cursor.fetchone()
                if not verify_result:
                    logging.getLogger(__name__).error(
                        "FY ID does not exist in database", extra={"fy_id": fy_id}
                    )
                    raise Exception(
                        f"Financial Year ID {fy_id} is invalid. Database integrity check failed. Please contact system administrator."
                    )

                verified_start_year, verified_end_year, verified_status = (
                    verify_result[1],
                    verify_result[2],
                    verify_result[3],
                )
                if verified_start_year != start_year or verified_end_year != end_year:
                    logging.getLogger(__name__).error(
                        "FY ID mismatch",
                        extra={
                            "fy_id": fy_id,
                            "expected": f"{start_year}-{end_year}",
                            "found": f"{verified_start_year}-{verified_end_year}",
                        },
                    )
                    raise Exception(
                        f"Financial Year ID {fy_id} data mismatch. Database integrity check failed. Please contact system administrator."
                    )

                logging.getLogger(__name__).debug(
                    "FY validation passed", extra={"fy_id": fy_id, "status": verified_status}
                )

                # Get period ID for the transaction date
                period_id = None
                if fy_id:
                    # Convert transaction date to string format for database query
                    date_str = transaction["date"].strftime("%Y-%m-%d")

                    # CRITICAL FIX: Ensure period belongs to the correct FY and exists in financial_years table
                    cursor.execute(
                        """
                        SELECT p.id FROM periods p
                        INNER JOIN financial_years fy ON p.fy_id = fy.id
                        WHERE p.fy_id = ? AND p.start_date <= ? AND p.end_date >= ?
                        ORDER BY p.period_number DESC LIMIT 1
                    """,
                        (fy_id, date_str, date_str),
                    )
                    period_result = cursor.fetchone()
                    period_id = period_result[0] if period_result else None

                    logging.getLogger(__name__).debug(
                        "Period lookup",
                        extra={"fy_id": fy_id, "date": date_str, "period_id": period_id},
                    )

                    # If no period found for this date, try to find the most recent open period for this FY
                    if period_id is None:
                        cursor.execute(
                            """
                            SELECT p.id FROM periods p
                            INNER JOIN financial_years fy ON p.fy_id = fy.id
                            WHERE p.fy_id = ? AND p.status = 'open'
                            ORDER BY p.period_number DESC LIMIT 1
                        """,
                            (fy_id,),
                        )
                        open_period_result = cursor.fetchone()
                        if open_period_result:
                            period_id = open_period_result[0]
                            logging.getLogger(__name__).info(
                                "Using open period as fallback",
                                extra={"fy_id": fy_id, "period_id": period_id},
                            )
                        else:
                            logging.getLogger(__name__).warning(
                                "No open periods found for FY",
                                extra={"fy_id": fy_id},
                            )

                # Get responsibility ID
                resp_id = None
                cursor.execute(
                    "SELECT id FROM responsibilities WHERE name = ?",
                    (transaction["responsibility"],),
                )
                resp_result = cursor.fetchone()
                resp_id = resp_result[0] if resp_result else None

                # Debug: Log responsibility lookup result
                if resp_id:
                    logging.getLogger(__name__).debug(
                        "Responsibility found",
                        extra={"name": transaction["responsibility"], "id": resp_id},
                    )
                else:
                    logging.getLogger(__name__).warning(
                        "Responsibility not found",
                        extra={"name": transaction["responsibility"]},
                    )

                # Use the case number that was already assigned during preview
                case_number = transaction.get("case_number")
                base_transaction_no = transaction.get("base_transaction_no", case_number)
                if not case_number:
                    logging.getLogger(__name__).debug("No case number assigned, using fallback")
                    # Fallback if no case number was assigned - use base_transaction_no for numbering
                    cursor.execute(
                        """
                        SELECT MAX(CAST(SUBSTR(base_transaction_no, -5) AS INTEGER))
                        FROM cases
                        WHERE fy_id = ?
                        AND fy_id IS NOT NULL
                        AND base_transaction_no IS NOT NULL
                        AND list != 'Deleted Cases'
                    """,
                        (fy_id,),
                    )
                    max_num = cursor.fetchone()[0]
                    next_num = (max_num or 0) + 1
                    fy_end_year = int(fy.split("-")[1])
                    case_number = f"FW-{fy_end_year}{next_num:05d}"
                    base_transaction_no = case_number

                logging.getLogger(__name__).debug(
                    "Prepared case identifiers",
                    extra={
                        "case_number": case_number,
                        "fy_id": fy_id,
                        "period_id": period_id,
                        "responsibility_id": resp_id,
                    },
                )

                # Prepare case data
                # date_str already defined above for period lookup

                # Debug: Log the actual values being inserted
                logging.getLogger(__name__).debug(
                    "Inserting case",
                    extra={
                        "transaction_no": case_number,
                        "responsibility_id": resp_id,
                        "category": self.category.get("name"),
                        "amount": abs(transaction["amount"]),
                        "fy_id": fy_id,
                        "period_id": period_id,
                    },
                )

                # Determine list and status based on transaction type
                if transaction["type"] == "GJ":
                    list_name = "Checklist"  # Will also be added to To-Do List
                    status = "Alleged"
                else:  # CL or AP
                    list_name = "Checklist"
                    status = "Alleged"

                # Clean transaction number
                clean_number = transaction["number"].lstrip("0") or "0"

                # Prepare description
                if transaction["type"] == "GJ":
                    description = f"{transaction['item']}. Journal authorised by BAS user {transaction['user_id']}"
                    bas_journal_no = clean_number
                    bas_journal_date = date_str
                    bas_payment_no = None
                    bas_payment_date = None
                elif transaction["type"] == "AP":
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

                # Optional: attempt to read default list ID (not required for insert)
                try:
                    cursor.execute(
                        "SELECT id FROM lists WHERE name = ? AND is_default = 1",
                        (list_name,),
                    )
                    list_result = cursor.fetchone()
                    _list_id_unused = list_result[0] if list_result else None
                except Exception:
                    # If lists table is missing, proceed using list_name string column
                    _list_id_unused = None

                # FINAL VALIDATION: Double-check fy_id before inserting
                cursor.execute(
                    "SELECT COUNT(*) FROM financial_years WHERE id = ?", (fy_id,)
                )
                fy_exists = cursor.fetchone()[0]
                if fy_exists == 0:
                    logging.getLogger(__name__).error(
                        "FY ID disappeared before insert", extra={"fy_id": fy_id}
                    )
                    raise Exception(
                        f"Critical database error: Financial Year ID {fy_id} no longer exists. Import aborted for safety."
                    )

                # Insert case - ensure NULL values are properly handled
                # Columns ordered to match physical table order to avoid SQLite column mapping issues
                logging.getLogger(__name__).debug(
                    "Executing INSERT for case", extra={"case_number": case_number, "fy_id": fy_id}
                )
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
                        case_number,
                        base_transaction_no,
                        date_str,
                        date_str,
                        date_str,
                        description,
                        bas_payment_no,
                        bas_payment_date,
                        None,
                        self.category["name"],
                        resp_id,
                        abs(transaction["amount"]),
                        None,
                        None,
                        None,  # Will set evidence later
                        status,
                        list_name,
                        None,
                        None,
                        None,
                        fy_id,
                        period_id,
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        list_name,
                        "[]",
                        None,
                        bas_journal_no,
                        bas_journal_date,
                    ),
                )

                case_id = cursor.lastrowid
                logging.getLogger(__name__).info(
                    "Case inserted",
                    extra={"case_number": case_number, "id": case_id, "fy_id": fy_id},
                )

                # Debug: Verify what was actually saved
                cursor.execute(
                    "SELECT fy_id, period_id, responsibility_id FROM cases WHERE id = ?",
                    (case_id,),
                )
                saved_values = cursor.fetchone()
                if saved_values:
                    saved_fy_id_check, saved_period_id_check, saved_resp_id = saved_values
                    logging.getLogger(__name__).debug(
                        "Post-insert verification",
                        extra={
                            "case_number": case_number,
                            "id": case_id,
                            "fy_id_saved": saved_fy_id_check,
                            "fy_id_expected": fy_id,
                            "period_id_saved": saved_period_id_check,
                            "period_id_expected": period_id,
                            "responsibility_id": saved_resp_id,
                        },
                    )

                    if saved_fy_id_check != fy_id:
                        logging.getLogger(__name__).error(
                            "fy_id mismatch after insert",
                            extra={"expected": fy_id, "saved": saved_fy_id_check},
                        )
                else:
                    logging.getLogger(__name__).error(
                        "Case not found by ID after insert", extra={"case_number": case_number}
                    )

                # Create case-specific supporting evidence folder
                year_folder = create_year_folder(fy)
                supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
                case_folder = os.path.join(supporting_evidence_folder, f"Case {case_number}")
                os.makedirs(case_folder, exist_ok=True)

                # Copy BAS file to proper location (not as evidence)
                if self.bas_file_path:
                    # Create Imported BAS Files folder structure
                    bas_files_folder = os.path.join(year_folder, "Imported BAS Files")

                    # Extract month from transaction date for subfolder (e.g., "202505")
                    month_str = transaction["date"].strftime("%Y%m")
                    month_folder = os.path.join(bas_files_folder, month_str)

                    # Create directories
                    os.makedirs(month_folder, exist_ok=True)

                    # Get original filename and copy with correct extension
                    original_filename = os.path.basename(self.bas_file_path)
                    bas_file_path = os.path.join(month_folder, original_filename)

                    # Copy file
                    shutil.copy2(self.bas_file_path, bas_file_path)

                    # Store BAS file path in source_document field
                    # Note: This will be a .txt file, not a PDF
                    cursor.execute(
                        "UPDATE cases SET source_document = ? WHERE transaction_no = ?",
                        (bas_file_path, case_number),
                    )

                    logging.getLogger(__name__).info(
                        "Copied BAS file", extra={"path": bas_file_path}
                    )

                # POST-INSERT VALIDATION: Verify the case was saved with correct fy_id
                logging.getLogger(__name__).debug(
                    "Validating saved case fy_id",
                    extra={"case_number": case_number, "expected_fy_id": fy_id},
                )
                cursor.execute(
                    "SELECT fy_id, id FROM cases WHERE transaction_no = ?", (case_number,)
                )
                validation_result = cursor.fetchone()
                logging.getLogger(__name__).debug(
                    "Validation result", extra={"result": validation_result}
                )

                if not validation_result:
                    logging.getLogger(__name__).error(
                        "Case not found after insert", extra={"case_number": case_number}
                    )
                    raise Exception(
                        f"Database integrity violation: Case not found after insert. Import aborted."
                    )

                saved_fy_id, saved_case_id = validation_result
                logging.getLogger(__name__).debug(
                    "Case saved fy_id",
                    extra={"case_number": case_number, "id": saved_case_id, "fy_id": saved_fy_id},
                )

                if saved_fy_id != fy_id:
                    logging.getLogger(__name__).error(
                        "Case saved with incorrect fy_id",
                        extra={"expected": fy_id, "saved": saved_fy_id, "case_number": case_number},
                    )

                    # Check if this is an orphaned case issue
                    cursor.execute(
                        "SELECT start_year, end_year FROM financial_years WHERE id = ?",
                        (saved_fy_id,),
                    )
                    fy_check = cursor.fetchone()
                    if not fy_check:
                        logging.getLogger(__name__).error(
                            "Saved fy_id does not exist (orphaned case)", extra={"fy_id": saved_fy_id}
                        )
                    else:
                        logging.getLogger(__name__).error(
                            "Saved fy_id exists but mismatched",
                            extra={"fy_start": fy_check[0], "fy_end": fy_check[1]},
                        )
                    raise Exception(
                        f"Database integrity violation: Case saved with incorrect financial year. Import aborted."
                    )

                logging.getLogger(__name__).debug(
                    "About to commit transaction for case", extra={"case_number": case_number}
                )
                # commit handled by context manager when exiting
                logging.getLogger(__name__).info(
                    "Successfully committed case", extra={"case_number": case_number}
                )

                # Log audit (convert all date objects to strings for JSON serialization)
                def convert_dates(obj):
                    if isinstance(obj, dict):
                        return {k: convert_dates(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_dates(item) for item in obj]
                    elif hasattr(obj, "isoformat"):  # Date/datetime objects
                        return obj.isoformat()
                    else:
                        return obj

                audit_transaction = convert_dates(transaction)

                return case_number
            finally:
                # Ensure the connection context manager exits properly
                try:
                    conn_ctx.__exit__(None, None, None)
                except Exception:
                    pass

            # Log audit after transaction is committed (outside the main connection)
            try:
                # Log audit (convert all date objects to strings for JSON serialization)
                def convert_dates(obj):
                    if isinstance(obj, dict):
                        return {k: convert_dates(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_dates(item) for item in obj]
                    elif hasattr(obj, "isoformat"):  # Date/datetime objects
                        return obj.isoformat()
                    else:
                        return obj

                audit_transaction = convert_dates(transaction)

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
            except Exception as audit_error:
                logging.getLogger(__name__).warning(f"Failed to save audit log: {audit_error}")

        except Exception:
            logging.getLogger(__name__).exception("Error importing transaction")
            return None
