import logging
from datetime import datetime

from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.db_utils import get_db_connection
from scripts.Utilities.financial_utils import (
    generate_transaction_no,
    get_financial_year,
)


class CaseService:
    """Service class for case management operations"""

    @staticmethod
    def create_case(case_data):
        """Create a new case in the database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

            # Insert case
            cursor.execute(
                """
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported,
                    description, bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date,
                    persal_no, category, responsibility_id, amount, source_document,
                    minutes, evidence_path, attachments, status, list, assessment_assessed_by,
                    assessment_date, assessment_result, fy_id, period_id, prevention_steps,
                    original_list, criminal_charges, disciplinary_process, loss_recovery
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_data.get("transaction_no"),
                    case_data.get("date_incurred"),
                    case_data.get("date_identified"),
                    case_data.get("date_reported"),
                    case_data.get("description"),
                    case_data.get("bas_payment_no"),
                    case_data.get("bas_payment_date"),
                    case_data.get("bas_journal_no"),
                    case_data.get("bas_journal_date"),
                    case_data.get("persal_no"),
                    case_data.get("category"),
                    case_data.get("responsibility_id"),
                    case_data.get("amount"),
                    case_data.get("source_document"),
                    case_data.get("minutes"),
                    case_data.get("evidence_path"),
                    case_data.get("attachments", "[]"),
                    case_data.get("status", "Alleged"),
                    case_data.get("list", "Checklist"),
                    case_data.get("assessment_assessed_by"),
                    case_data.get("assessment_date"),
                    case_data.get("assessment_result"),
                    case_data.get("fy_id"),
                    case_data.get("period_id"),
                    case_data.get("prevention_steps"),
                    case_data.get("original_list", case_data.get("list", "Checklist")),
                    case_data.get("criminal_charges", "N/A"),
                    case_data.get("disciplinary_process", "N/A"),
                    case_data.get("loss_recovery", "N/A"),
                ),
            )

            case_id = cursor.lastrowid

            # Log audit trail
            save_audit_log(
                "create_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": case_data.get("transaction_no"),
                    "details": case_data,
                },
                get_financial_year(),
            )

            return case_id

        except Exception as e:
            logging.getLogger(__name__).exception("Error creating case")
            raise

    @staticmethod
    def update_case(case_id, case_data):
        """Update an existing case"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

            # Update case
            cursor.execute(
                """
                UPDATE cases SET
                    date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                    bas_payment_no = ?, bas_payment_date = ?, bas_journal_no = ?, bas_journal_date = ?,
                    persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                    source_document = ?, minutes = ?, evidence_path = ?, attachments = ?,
                    status = ?, list = ?, assessment_assessed_by = ?, assessment_date = ?,
                    assessment_result = ?, criminal_charges = ?, disciplinary_process = ?,
                    loss_recovery = ?, prevention_steps = ?, original_list = ?
                WHERE id = ?
            """,
                (
                    case_data.get("date_incurred"),
                    case_data.get("date_identified"),
                    case_data.get("date_reported"),
                    case_data.get("description"),
                    case_data.get("bas_payment_no"),
                    case_data.get("bas_payment_date"),
                    case_data.get("bas_journal_no"),
                    case_data.get("bas_journal_date"),
                    case_data.get("persal_no"),
                    case_data.get("category"),
                    case_data.get("responsibility_id"),
                    case_data.get("amount"),
                    case_data.get("source_document"),
                    case_data.get("minutes"),
                    case_data.get("evidence_path"),
                    case_data.get("attachments", "[]"),
                    case_data.get("status"),
                    case_data.get("list"),
                    case_data.get("assessment_assessed_by"),
                    case_data.get("assessment_date"),
                    case_data.get("assessment_result"),
                    case_data.get("criminal_charges"),
                    case_data.get("disciplinary_process"),
                    case_data.get("loss_recovery"),
                    case_data.get("prevention_steps"),
                    case_data.get("original_list"),
                    case_id,
                ),
            )

            # Log audit trail
            save_audit_log(
                "update_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": case_data.get("transaction_no"),
                    "details": case_data,
                },
                get_financial_year(),
            )

            return True

        except Exception as e:
            logging.getLogger(__name__).exception("Error updating case")
            raise

    @staticmethod
    def delete_case(case_id, transaction_no):
        """Delete case by moving it to Deleted Cases"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

            # Get current list before updating
            cursor.execute("SELECT list FROM cases WHERE id = ?", (case_id,))
            current_list_result = cursor.fetchone()
            current_list = current_list_result[0] if current_list_result else "Unknown"

            # Update case to Deleted Cases
            cursor.execute(
                """
                UPDATE cases
                SET list = 'Deleted Cases', original_list = ?
                WHERE id = ?
            """,
                (current_list, case_id),
            )

            # Log audit trail
            save_audit_log(
                "delete_case",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": transaction_no,
                    "original_list": current_list,
                    "details": "Case moved to Deleted Cases",
                },
                get_financial_year(),
            )

            return True

        except Exception as e:
            logging.getLogger(__name__).exception("Error deleting case")
            raise

    @staticmethod
    def get_case_by_id(case_id):
        """Get case data by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
                case_data = cursor.fetchone()
                columns = (
                    [desc[0] for desc in cursor.description] if case_data else None
                )

            if case_data and columns:
                # Convert to dictionary for easier handling
                return dict(zip(columns, case_data))
            return None

        except Exception as e:
            logging.getLogger(__name__).exception("Error getting case by id")
            return None

    @staticmethod
    def get_case_by_transaction_no(transaction_no):
        """Get case data by transaction number"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM cases WHERE transaction_no = ?", (transaction_no,)
                )
                case_data = cursor.fetchone()
                columns = (
                    [desc[0] for desc in cursor.description] if case_data else None
                )

            if case_data and columns:
                # Convert to dictionary for easier handling
                return dict(zip(columns, case_data))
            return None

        except Exception as e:
            logging.getLogger(__name__).exception(
                "Error getting case by transaction number"
            )
            return None

    @staticmethod
    def validate_case_data(case_data):
        """Validate case data before saving"""
        errors = []

        # Required fields
        if not case_data.get("description", "").strip():
            errors.append("Description is required")

        if not case_data.get("category"):
            errors.append("Category is required")

        if not case_data.get("responsibility_id"):
            errors.append("Responsibility is required")

        if case_data.get("amount") is None or case_data.get("amount") <= 0:
            errors.append("Valid amount is required")

        # Date validations
        required_dates = ["date_incurred", "date_identified", "date_reported"]
        for date_field in required_dates:
            if not case_data.get(date_field):
                errors.append(f"{date_field.replace('_', ' ').title()} is required")

        return errors

    @staticmethod
    def generate_case_number():
        """Generate a new case number"""
        return generate_transaction_no(get_financial_year())

    @staticmethod
    def find_duplicate_cases(
        responsibility_id, category, amount, fy_id, exclude_case_id=None
    ):
        """Find potential duplicate cases"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

            query = """
                SELECT * FROM cases
                WHERE responsibility_id = ?
                  AND category = ?
                  AND ABS(amount - ?) < 0.01
                  AND fy_id = ?
                  AND list != 'Deleted Cases'
            """
            params = [responsibility_id, category, amount, fy_id]

            if exclude_case_id:
                query += " AND id != ?"
                params.append(exclude_case_id)

            cursor.execute(query, params)
            duplicates = cursor.fetchall()

            return duplicates

        except Exception as e:
            logging.getLogger(__name__).exception("Error finding duplicates")
            return []
