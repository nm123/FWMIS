"""
Validation utilities for undisclosed imports.
"""
import sqlite3
from scripts.Utilities.config import DB_PATH


def validate_responsibility(responsibility_name):
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


def validate_financial_year(fy_string):
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