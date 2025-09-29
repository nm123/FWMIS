"""
Transaction Processor Module for Import Operations

Contains the logic for processing individual transactions during import.
"""

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .worker_base import ImportWorker


class TransactionProcessor:
    """
    Processes individual transactions during import operations.
    """

    @staticmethod
    def import_transaction(worker: "ImportWorker", transaction: Dict) -> str:
        """
        Import a single transaction as a case.

        Args:
            worker: The ImportWorker instance
            transaction: Transaction dictionary to import

        Returns:
            str: Generated case number if successful, empty string otherwise
        """
        try:
            import os
            import shutil
            from datetime import datetime

            from scripts.Utilities.audit_utils import save_audit_log
            from scripts.Utilities.db_utils import get_db_connection
            from scripts.Utilities.financial_utils import (
                create_year_folder,
                get_financial_year,
            )
            from scripts.Utilities.responsibility_utils import (
                load_posting_responsibilities,
            )

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # Extract transaction data
                case_number = transaction.get("case_number", "")
                amount = transaction.get("amount", 0)
                description = transaction.get("description", "")
                reference_no = transaction.get("reference_no", "")
                transaction_date = transaction.get("date", "")

                # Validate required fields
                if not case_number or not amount:
                    return ""

                # Determine financial year
                fy = worker.selected_fy
                if not fy:
                    fy = get_financial_year()
                    if not fy:
                        return ""

                # Get fy_id from fy string
                cursor.execute(
                    "SELECT id FROM financial_years WHERE start_year || '-' || end_year = ?",
                    (fy,)
                )
                fy_result = cursor.fetchone()
                fy_id = fy_result[0] if fy_result else None
                if not fy_id:
                    return ""

                # Use the pre-assigned case number as transaction number
                transaction_no = case_number

                # Get posting responsibilities for assignment
                posting_responsibilities = load_posting_responsibilities()
                if not posting_responsibilities:
                    return ""

                # Use the first available posting responsibility
                responsibility_id = posting_responsibilities[0]["id"]

                # Prepare case data
                case_data = {
                    "transaction_no": transaction_no,
                    "description": description,
                    "bas_payment_no": reference_no,  # Use bas_payment_no instead of reference_no
                    "category": worker.category.get("name"),  # Use category name, not id
                    "responsibility_id": responsibility_id,
                    "amount": float(amount),
                    "status": "Alleged",
                    "fy_id": fy_id,  # Use the looked-up fy_id
                    "date_reported": transaction_date,  # Use date_reported instead of transaction_date
                }

                # Insert case into database
                cursor.execute(
                    """
                    INSERT INTO cases (
                        transaction_no, description, bas_payment_no, category,
                        responsibility_id, amount, status, fy_id, date_reported
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        case_data["transaction_no"],
                        case_data["description"],
                        case_data["bas_payment_no"],
                        case_data["category"],
                        case_data["responsibility_id"],
                        case_data["amount"],
                        case_data["status"],
                        case_data["fy_id"],
                        case_data["date_reported"],
                    ),
                )

                case_id = cursor.lastrowid

                # Handle BAS file copy if provided
                if worker.bas_file_path and os.path.exists(worker.bas_file_path):
                    year_folder = create_year_folder(fy)
                    if year_folder:
                        # Generate BAS filename
                        bas_filename = f"{transaction_no}_BAS.pdf"
                        bas_dest_path = os.path.join(year_folder, bas_filename)

                        try:
                            shutil.copy2(worker.bas_file_path, bas_dest_path)

                            # Update case with BAS file path
                            cursor.execute(
                                """
                                UPDATE cases
                                SET bas_document_path = ?
                                WHERE id = ?
                            """,
                                (bas_dest_path, case_id),
                            )

                        except Exception as e:
                            # Log but don't fail the import
                            print(
                                f"Warning: Failed to copy BAS file for case {transaction_no}: {e}"
                            )

                # Create status history entry
                cursor.execute(
                    """
                    INSERT INTO case_status_history (
                        case_id, old_status, new_status, changed_date, changed_by
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        case_id,
                        None,
                        "Alleged",
                        datetime.now().isoformat(),
                        "Import Process",
                    ),
                )

                conn.commit()

                # Log the import
                save_audit_log(
                    "CASE_IMPORTED",
                    f"Case {transaction_no} imported from BAS data",
                    case_id,
                )

                return transaction_no

            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

        except Exception as e:
            print(
                f"Error importing transaction {transaction.get('case_number', 'Unknown')}: {e}"
            )
            return ""
