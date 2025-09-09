import os
import sqlite3
import shutil
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year, generate_transaction_no, create_year_folder
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.responsibility_utils import load_posting_responsibilities


class ImportWorker(QThread):
    """Worker thread for importing cases"""
    progress = pyqtSignal(int, str)  # progress percentage, current operation
    finished = pyqtSignal(list)  # list of imported case numbers
    error = pyqtSignal(str)

    def __init__(self, transactions, category, date_from, date_to, bas_file_path):
        super().__init__()
        self.transactions = transactions
        self.category = category
        self.date_from = date_from
        self.date_to = date_to
        self.bas_file_path = bas_file_path

    def run(self):
        try:
            imported_cases = []
            total = len(self.transactions)
            print(f"DEBUG: ImportWorker starting with {total} transactions")

            for i, transaction in enumerate(self.transactions):
                try:
                    self.progress.emit(int((i / total) * 100), f"Importing case {i+1} of {total}...")
                    print(f"DEBUG: Processing transaction {i+1}: {transaction.get('case_number', 'No case number')}")

                    # Import the transaction as a case
                    case_number = self._import_transaction(transaction)
                    if case_number:
                        imported_cases.append(case_number)
                        print(f"DEBUG: Successfully imported case: {case_number}")
                    else:
                        print(f"DEBUG: Failed to import transaction {i+1}")
                        # Continue with other transactions even if one fails
                        continue

                except Exception as e:
                    print(f"DEBUG: Error importing transaction {i+1}: {e}")
                    import traceback
                    print(f"DEBUG: Transaction error traceback: {traceback.format_exc()}")
                    # Continue with other transactions
                    continue

            print(f"DEBUG: Import completed. Successfully imported {len(imported_cases)} cases")
            self.progress.emit(100, "Import completed successfully")
            self.finished.emit(imported_cases)

        except Exception as e:
            print(f"DEBUG: ImportWorker critical error: {e}")
            import traceback
            print(f"DEBUG: ImportWorker traceback: {traceback.format_exc()}")
            self.error.emit(f"Critical import error: {str(e)}")

    def _import_transaction(self, transaction):
        """Import a single transaction as a case"""
        try:
            print(f"DEBUG: _import_transaction called for: {transaction.get('case_number', 'No case number')}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Get financial year ID
            cursor.execute("SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?", (start_year, end_year))
            fy_result = cursor.fetchone()
            fy_id = fy_result[0] if fy_result else None

            print(f"DEBUG: Import - Current FY: {fy}, start_year: {start_year}, end_year: {end_year}, fy_id: {fy_id}")

            # CRITICAL: Check if fy_id is valid before proceeding
            if fy_id is None:
                print(f"DEBUG: *** CRITICAL ERROR *** FY {fy} not found in database!")
                print(f"DEBUG: This will cause cases to be imported with invalid fy_id")
                conn.close()
                raise Exception(f"Financial Year {fy} not found in database. Please ensure the financial year is properly set up in Financial Year Management before importing cases.")
            else:
                print(f"DEBUG: Found FY {fy} with ID: {fy_id}")

            # Get period ID for the transaction date
            period_id = None
            if fy_id:
                # Convert transaction date to string format for database query
                date_str = transaction['date'].strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT id FROM periods
                    WHERE fy_id = ? AND start_date <= ? AND end_date >= ?
                    ORDER BY period_number DESC LIMIT 1
                """, (fy_id, date_str, date_str))
                period_result = cursor.fetchone()
                period_id = period_result[0] if period_result else None

                # If no period found for this date, try to find the most recent open period for this FY
                if period_id is None:
                    cursor.execute("""
                        SELECT id FROM periods
                        WHERE fy_id = ? AND status = 'open'
                        ORDER BY period_number DESC LIMIT 1
                    """, (fy_id,))
                    open_period_result = cursor.fetchone()
                    if open_period_result:
                        period_id = open_period_result[0]
                        print(f"DEBUG: Using open period {period_id} for FY {fy_id} as fallback")
                    else:
                        print(f"DEBUG: No open periods found for FY {fy_id}, using period_id = None")

            # Get responsibility ID
            resp_id = None
            cursor.execute("SELECT id FROM responsibilities WHERE name = ?", (transaction['responsibility'],))
            resp_result = cursor.fetchone()
            resp_id = resp_result[0] if resp_result else None

            # Debug: Log responsibility lookup result
            if resp_id:
                print(f"DEBUG: Found responsibility '{transaction['responsibility']}' with ID: {resp_id}")
            else:
                print(f"DEBUG: Responsibility '{transaction['responsibility']}' NOT found in database")

            # Use the case number that was already assigned during preview
            case_number = transaction.get('case_number')
            if not case_number:
                print("DEBUG: No case number assigned, using fallback")
                # Fallback if no case number was assigned
                cursor.execute("SELECT MAX(CAST(SUBSTR(transaction_no, 5) AS INTEGER)) FROM cases WHERE transaction_no LIKE ?", (f"{fy}%",))
                max_num = cursor.fetchone()[0]
                next_num = (max_num or 0) + 1
                fy_end_year = int(fy.split('-')[1])
                case_number = f"{fy_end_year}{next_num:05d}"

            print(f"DEBUG: Using case number: {case_number}, fy_id: {fy_id}, period_id: {period_id}, resp_id: {resp_id}")

            # Prepare case data
            # date_str already defined above for period lookup

            # Debug: Log the actual values being inserted
            print(f"DEBUG: Inserting case with values:")
            print(f"  - transaction_no: {case_number}")
            print(f"  - responsibility_id: {resp_id}")
            print(f"  - category: {self.category['name']}")
            print(f"  - amount: {abs(transaction['amount'])}")
            print(f"  - fy_id: {fy_id}")
            print(f"  - period_id: {period_id}")

            # Determine list and status based on transaction type
            if transaction['type'] == 'GJ':
                list_name = 'Checklist'  # Will also be added to To-Do List
                status = 'Alleged'
            else:  # CL or AP
                list_name = 'Checklist'
                status = 'Alleged'

            # Clean transaction number
            clean_number = transaction['number'].lstrip('0') or '0'

            # Prepare description
            if transaction['type'] == 'GJ':
                description = f"{transaction['item']}. Journal authorised by BAS user {transaction['user_id']}"
                bas_journal_no = clean_number
                bas_journal_date = date_str
                bas_payment_no = None
                bas_payment_date = None
            elif transaction['type'] == 'AP':
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

            # Get default list ID
            cursor.execute("SELECT id FROM lists WHERE name = ? AND is_default = 1", (list_name,))
            list_result = cursor.fetchone()
            list_id = list_result[0] if list_result else 1

            # Insert case - ensure NULL values are properly handled
            cursor.execute("""
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported,
                    description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category,
                    responsibility_id, amount, source_document, minutes, evidence_path,
                    attachments, status, list, assessment_assessed_by, assessment_date,
                    assessment_result, fy_id, period_id, criminal_charges, disciplinary_process,
                    loss_recovery, prevention_steps, original_list
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_number, date_str, date_str, date_str,
                description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, None, self.category['name'],
                resp_id, abs(transaction['amount']), None, None, None,  # Will set evidence later
                '[]', status, list_name, None, None,
                fy_id, period_id, 'N/A', 'N/A', 'N/A',
                'N/A', 'N/A', list_name
            ))

            case_id = cursor.lastrowid

            # Debug: Verify what was actually saved
            cursor.execute("SELECT responsibility_id FROM cases WHERE id = ?", (case_id,))
            saved_resp_id = cursor.fetchone()
            print(f"DEBUG: Case {case_number} saved with responsibility_id: {saved_resp_id[0] if saved_resp_id else 'None'}")


            # Copy BAS file to proper location (not as evidence)
            if self.bas_file_path:
                # Create Imported BAS Files folder structure
                year_folder = create_year_folder(fy)
                bas_files_folder = os.path.join(year_folder, "Imported BAS Files")

                # Extract month from transaction date for subfolder (e.g., "202505")
                month_str = transaction['date'].strftime('%Y%m')
                month_folder = os.path.join(bas_files_folder, month_str)

                # Create directories
                os.makedirs(month_folder, exist_ok=True)

                # Get original filename and copy with correct extension
                original_filename = os.path.basename(self.bas_file_path)
                bas_file_path = os.path.join(month_folder, original_filename)

                # Copy file
                shutil.copy2(self.bas_file_path, bas_file_path)

                # Store BAS file path in source_document field instead of evidence_path
                cursor.execute("UPDATE cases SET source_document = ? WHERE transaction_no = ?",
                              (bas_file_path, case_number))

                print(f"DEBUG: Copied BAS file to: {bas_file_path}")

            print(f"DEBUG: About to commit transaction for case: {case_number}")
            conn.commit()
            conn.close()
            print(f"DEBUG: Successfully committed case: {case_number}")

            # Log audit (convert all date objects to strings for JSON serialization)
            def convert_dates(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates(item) for item in obj]
                elif hasattr(obj, 'isoformat'):  # Date/datetime objects
                    return obj.isoformat()
                else:
                    return obj

            audit_transaction = convert_dates(transaction)

            save_audit_log("import_undisclosed_case", {
                "timestamp": datetime.now().isoformat(),
                "case_number": case_number,
                "transaction": audit_transaction,
                "category": self.category['name']
            }, fy)

            return case_number

        except Exception as e:
            print(f"DEBUG: Error importing transaction: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            # Ensure database connection is properly closed on error
            if 'conn' in locals():
                try:
                    conn.rollback()  # Rollback any pending transaction
                    conn.close()
                except:
                    pass
            return None