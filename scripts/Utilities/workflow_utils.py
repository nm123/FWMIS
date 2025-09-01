import sqlite3
from datetime import datetime
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year

def handle_case_status_change(case_id, transaction_no, new_status, new_list=None, user_id=None):
    """
    Handle automatic workflow transitions based on status changes

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        new_status: New status being set
        new_list: New list (optional, will be determined automatically if not provided)
        user_id: User making the change (optional)
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current case data
        cursor.execute("SELECT list, status, is_finalized FROM cases WHERE id = ?", (case_id,))
        current_data = cursor.fetchone()

        if not current_data:
            return False

        current_list, current_status, is_finalized = current_data

        # Prevent changes to finalized cases
        if is_finalized:
            return False

        # Determine automatic list changes based on status
        automatic_list = new_list

        if new_status == "Recovered":
            automatic_list = "Recovered"
        elif new_status == "Write Off Recommended":
            automatic_list = "Write-Off Recommended"
        elif new_status == "Written Off":
            automatic_list = "Written Off"

        # Handle finalization logic
        should_finalize = False
        finalization_reason = None

        if new_status in ["Recovered", "Written Off"]:
            should_finalize = True
            finalization_reason = f"Case {new_status.lower()}"

        # Apply changes
        update_fields = ["status = ?"]
        update_values = [new_status]

        if automatic_list and automatic_list != current_list:
            update_fields.append("list = ?")
            update_values.append(automatic_list)

        if should_finalize:
            update_fields.append("is_finalized = ?")
            update_fields.append("finalized_date = ?")
            update_fields.append("finalization_reason = ?")
            update_values.extend([1, datetime.now().strftime("%Y-%m-%d"), finalization_reason])

        update_values.append(case_id)

        if update_fields:
            query = f"UPDATE cases SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)

            # Log the workflow change
            workflow_data = {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "transaction_no": transaction_no,
                "previous_status": current_status,
                "new_status": new_status,
                "previous_list": current_list,
                "new_list": automatic_list or current_list,
                "finalized": should_finalize,
                "user_id": user_id
            }

            save_audit_log("workflow_transition", workflow_data, get_financial_year())

        conn.commit()
        return True

    except Exception as e:
        print(f"Error in handle_case_status_change: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_case_workflow_status(case_id):
    """
    Get comprehensive workflow status for a case

    Returns:
        dict: Workflow status information
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT c.status, c.list, c.is_finalized, c.finalized_date,
                   c.determination_amount, c.determination_date,
                   c.committee_recommendations, c.write_off_submission_id,
                   dh.determination_date as last_determination_date
            FROM cases c
            LEFT JOIN determination_history dh ON c.id = dh.case_id
            WHERE c.id = ?
            ORDER BY dh.determination_date DESC LIMIT 1
        """, (case_id,))

        result = cursor.fetchone()
        if result:
            status, list_name, is_finalized, finalized_date, determination_amount, determination_date, committee_recommendations, write_off_submission_id, last_determination_date = result

            return {
                "current_status": status,
                "current_list": list_name,
                "is_finalized": bool(is_finalized),
                "finalized_date": finalized_date,
                "has_determination": determination_amount is not None,
                "determination_amount": determination_amount,
                "determination_date": determination_date,
                "last_determination_date": last_determination_date,
                "committee_recommendations": committee_recommendations,
                "write_off_submission_id": write_off_submission_id,
                "can_edit": not bool(is_finalized),
                "can_determine": list_name == "Lead Schedule" and status == "Confirmed" and not determination_amount,
                "can_recover": list_name == "Lead Schedule" and determination_amount is not None,
                "can_write_off": list_name == "Write-Off Recommended"
            }

        return None

    except Exception as e:
        print(f"Error getting case workflow status: {e}")
        return None
    finally:
        conn.close()

def check_workflow_completion():
    """
    Check for cases that need workflow attention
    Returns list of cases needing action
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Cases in Lead Schedule that need determination
        cursor.execute("""
            SELECT transaction_no, status, list
            FROM cases
            WHERE list = 'Lead Schedule'
            AND status = 'Confirmed'
            AND determination_amount IS NULL
            AND is_finalized = 0
        """)

        needs_determination = cursor.fetchall()

        # Cases recommended for write-off that need submission
        cursor.execute("""
            SELECT transaction_no, status, list
            FROM cases
            WHERE list = 'Write-Off Recommended'
            AND write_off_submission_id IS NULL
            AND is_finalized = 0
        """)

        needs_submission = cursor.fetchall()

        return {
            "needs_determination": needs_determination,
            "needs_write_off_submission": needs_submission
        }

    except Exception as e:
        print(f"Error checking workflow completion: {e}")
        return {"needs_determination": [], "needs_write_off_submission": []}
    finally:
        conn.close()