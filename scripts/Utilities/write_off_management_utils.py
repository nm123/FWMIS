"""
Utilities for managing write-off submissions.
"""

import sqlite3

from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.workflow_utils import approve_write_off_submission


def get_evidence_status(evidence_paths):
    """Get a summary of evidence status"""
    if not evidence_paths:
        return "No evidence"

    try:
        import json

        evidence = json.loads(evidence_paths)
        evidence_types = []
        if evidence.get("assessment"):
            evidence_types.append("Assessment")
        if evidence.get("lc_minutes"):
            evidence_types.append("LC Minutes")
        if evidence.get("recovery"):
            evidence_types.append("Recovery")

        return ", ".join(evidence_types) if evidence_types else "No evidence"
    except Exception as e:
        import logging

        logging.warning(f"Failed to parse evidence data '{evidence}': {e}")
        return "Invalid evidence data"


def load_group_details(group_id):
    """Load details of the write-off group and return summary and cases"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get group summary
        cursor.execute(
            """
            SELECT COUNT(*), SUM(amount)
            FROM cases
            WHERE write_off_group_id = ?
        """,
            (group_id,),
        )

        summary = cursor.fetchone()
        case_count, total_amount = summary if summary else (0, 0)
        formatted_amount = format_currency_amount(total_amount or 0)
        summary_text = (
            f"Group ID: {group_id}\n"
            f"Total Cases: {case_count}\n"
            f"Total Amount: {formatted_amount}"
        )

        # Get case details
        cursor.execute(
            """
            SELECT base_transaction_no, category, amount, assessment_status, evidence_paths
            FROM cases
            WHERE write_off_group_id = ?
            ORDER BY base_transaction_no
        """,
            (group_id,),
        )

        cases = cursor.fetchall()
        case_list = []
        for case_data in cases:
            base_transaction_no, category, amount, assessment_status, evidence_paths = (
                case_data
            )
            amount_formatted = format_currency_amount(amount, right_align=True)
            evidence_status = get_evidence_status(evidence_paths)
            case_list.append(
                {
                    "case_no": base_transaction_no,
                    "category": str(category) if category else "",
                    "amount": amount_formatted,
                    "assessment_status": assessment_status or "",
                    "evidence": evidence_status,
                }
            )

        return summary_text, case_list

    except Exception as e:
        raise e
    finally:
        conn.close()


def approve_write_off(group_id, notes=""):
    """Approve the write-off submission"""
    try:
        success = approve_write_off_submission(group_id)
        if success and notes:
            # Save audit log with notes
            save_audit_log(f"Write-off submission {group_id} approved. Notes: {notes}")
        return success
    except Exception as e:
        raise e
