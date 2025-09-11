import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year, create_year_folder
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.workflow_utils import handle_case_status_change


class CaseBusinessLogic:
    """Business logic methods for case management"""

    def __init__(self, fy):
        self.fy = fy

    def validate_responsibility(self, responsibility_name):
        """Validate if responsibility exists and is posting level"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_posting_level FROM responsibilities WHERE name = ?", (responsibility_name,))
            result = cursor.fetchone()
            conn.close()

            if result:
                resp_id, is_posting = result
                if is_posting:
                    return {'status': 'Valid', 'id': resp_id}
                else:
                    return {'status': 'Non-Posting', 'id': resp_id}
            else:
                return {'status': 'Not Found', 'id': None}

        except sqlite3.Error as e:
            print(f"Error validating responsibility: {e}")
            return {'status': 'Error', 'id': None}

    def validate_financial_year(self, fy_string):
        """Validate if financial year exists in database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Parse FY string (e.g., "2025-2026")
            fy_parts = fy_string.split('-')
            if len(fy_parts) != 2:
                return {'exists': False, 'fy_id': None, 'status': 'Invalid format'}

            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            cursor.execute("SELECT id, status FROM financial_years WHERE start_year = ? AND end_year = ?",
                          (start_year, end_year))
            result = cursor.fetchone()
            conn.close()

            if result:
                fy_id, status = result
                return {
                    'exists': True,
                    'fy_id': fy_id,
                    'status': status,
                    'fy_string': fy_string
                }
            else:
                return {
                    'exists': False,
                    'fy_id': None,
                    'status': 'Not Found',
                    'fy_string': fy_string
                }

        except sqlite3.Error as e:
            print(f"Error validating financial year: {e}")
            return {'exists': False, 'fy_id': None, 'status': 'Error', 'fy_string': fy_string}
        except ValueError as e:
            print(f"Error parsing financial year string '{fy_string}': {e}")
            return {'exists': False, 'fy_id': None, 'status': 'Invalid format', 'fy_string': fy_string}

    def check_period_status(self, date_from, date_to):
        """Check if the period for the selected date range is open"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year for the date range
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Find the period that contains the date range
            cursor.execute("""
                SELECT p.id, p.period_number, p.status, p.start_date, p.end_date
                FROM periods p
                WHERE p.fy_id = (SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?)
                  AND p.start_date <= ? AND p.end_date >= ?
            """, (start_year, end_year, date_to, date_from))

            period = cursor.fetchone()
            conn.close()

            if period:
                return {
                    'id': period[0],
                    'period_number': period[1],
                    'status': period[2],
                    'start_date': period[3],
                    'end_date': period[4],
                    'period_name': f"Period {period[1]}"
                }
            else:
                return {'status': 'not_found', 'period_name': 'Unknown'}

        except sqlite3.Error as e:
            print(f"Error checking period status: {e}")
            return {'status': 'error', 'period_name': 'Error'}

    def get_current_open_period(self):
        """Get the current open period"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year
            fy = get_financial_year()
            fy_parts = fy.split('-')
            start_year = int(fy_parts[0])
            end_year = int(fy_parts[1])

            # Find the currently open period
            cursor.execute("""
                SELECT id, period_number, start_date, end_date
                FROM periods
                WHERE fy_id = (SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?)
                  AND status = 'open'
                ORDER BY period_number DESC
                LIMIT 1
            """, (start_year, end_year))

            period = cursor.fetchone()
            conn.close()

            if period:
                return {
                    'id': period[0],
                    'period_number': period[1],
                    'start_date': period[2],
                    'end_date': period[3]
                }
            else:
                return None

        except sqlite3.Error as e:
            print(f"Error getting current open period: {e}")
            return None

    def is_valid_status_transition(self, current_list, current_status, new_status):
        """Validate if a status transition is allowed based on workflow rules"""
        if current_status == new_status:
            return True  # Allow staying in same status

        # Define valid transitions for each list
        valid_transitions = {
            "Checklist": {
                "Alleged": ["Under Assessment", "Valid", "Confirmed"],
                "Under Assessment": ["Valid", "Confirmed"],
                "Valid": [],  # End state
                "Confirmed": []  # Should be copied to Lead Schedule
            },
            "Lead Schedule": {
                "Awaiting LC determination": ["Recovered", "Write Off"],
                "Recovered": [],  # End state
                "Write Off": []  # Should be copied to Write-Off Recommended
            },
            "Write-Off Recommended": {
                "Write Off Recommended": ["Written Off"],
                "Written Off": []  # End state
            },
            "Recovered": {
                "Recovered": []  # End state
            },
            "Written Off": {
                "Written Off": []  # End state
            }
        }

        # Get valid transitions for current list and status
        list_transitions = valid_transitions.get(current_list, {})
        allowed_transitions = list_transitions.get(current_status, [])

        return new_status in allowed_transitions