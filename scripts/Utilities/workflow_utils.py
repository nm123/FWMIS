import sqlite3
from datetime import datetime
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year

def handle_loss_control_status_change(case_id, transaction_no, loss_control_status, user_id=None):
    """
    Handle automatic workflow transitions based on Loss Control status changes

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        loss_control_status: New Loss Control status ("Recovered" or "Write Off Recommended")
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """

    print(f"DEBUG: handle_loss_control_status_change called for case_id: {case_id}, transaction_no: {transaction_no}, loss_control_status: {loss_control_status}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current case data
        cursor.execute("SELECT list, status, is_finalized, fy_id FROM cases WHERE id = ?", (case_id,))
        current_data = cursor.fetchone()

        if not current_data:
            print(f"DEBUG: Case {case_id} not found")
            return False

        current_list, current_status, is_finalized, fy_id = current_data
        print(f"DEBUG: Case {case_id} current list: {current_list}, status: {current_status}, fy_id: {fy_id}")

        # Prevent changes to finalized cases
        if is_finalized:
            return False

        # Handle Loss Control status changes
        if loss_control_status == "Recovered":
            # Copy case to Recovered list
            print(f"DEBUG: Copying case {case_id} ({transaction_no}) to Recovered")
            conn.commit()
            conn.close()
            return copy_case_to_recovered(case_id, transaction_no, user_id)

        elif loss_control_status == "Write Off Recommended":
            # Copy case to Write-Off Recommended list
            print(f"DEBUG: Copying case {case_id} ({transaction_no}) to Write-Off Recommended")
            conn.commit()
            conn.close()
            return copy_case_to_write_off_recommended_from_lead_schedule(case_id, transaction_no, user_id)

        return True

    except Exception as e:
        print(f"Error in handle_loss_control_status_change: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


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

    print(f"DEBUG: handle_case_status_change called for case_id: {case_id}, transaction_no: {transaction_no}, new_status: {new_status}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current case data including fy_id
        cursor.execute("SELECT list, status, is_finalized, fy_id FROM cases WHERE id = ?", (case_id,))
        current_data = cursor.fetchone()

        if not current_data:
            print(f"DEBUG: Case {case_id} not found")
            return False

        current_list, current_status, is_finalized, fy_id = current_data
        print(f"DEBUG: Case {case_id} current list: {current_list}, status: {current_status}, fy_id: {fy_id}")

        # Prevent changes to finalized cases
        if is_finalized:
            return False

        # Handle automatic list changes based on status
        automatic_list = new_list

        # Determine automatic list changes based on status
        automatic_list = new_list

        # Validate fy_id before making any workflow changes
        if fy_id is None or fy_id not in [fy[0] for fy in cursor.execute("SELECT id FROM financial_years").fetchall()]:
            print(f"DEBUG: Invalid fy_id {fy_id} detected for case {transaction_no}, fixing...")
            # Get current financial year ID
            from scripts.Utilities.financial_utils import get_current_open_financial_year
            current_fy = get_current_open_financial_year()
            if current_fy:
                fy_id = current_fy[0]
                print(f"DEBUG: Fixed fy_id to {fy_id} for case {transaction_no}")
                # Update the case's fy_id in the database
                cursor.execute("UPDATE cases SET fy_id = ? WHERE id = ?", (fy_id, case_id))
                conn.commit()
            else:
                print(f"ERROR: Cannot update case {transaction_no} - no open financial year found")
                return False

        if new_status == "Confirmed" and current_list == "Checklist":
            # Copy case to Lead Schedule when status changes to Confirmed
            print(f"DEBUG: Copying case {case_id} ({transaction_no}) to Lead Schedule")
            # Close connection before calling copy function to avoid connection issues
            conn.commit()
            conn.close()
            return copy_case_to_lead_schedule(case_id, transaction_no, user_id)
        elif new_status == "Recovered":
            automatic_list = "Recovered"
        elif new_status == "Write Off":
            # For Write Off, copy to Write-Off Recommended list
            print(f"DEBUG: Copying case {case_id} ({transaction_no}) to Write-Off Recommended")
            # Close connection before calling copy function to avoid connection issues
            conn.commit()
            conn.close()
            return copy_case_to_write_off_recommended(case_id, transaction_no, user_id)
        elif new_status == "Written Off":
            if current_list == "Write-Off Recommended":
                automatic_list = "Written Off"
            else:
                automatic_list = "Written Off"

        # Handle finalization logic
        should_finalize = False
        finalization_reason = None

        if new_status in ["Valid", "Recovered", "Written Off"]:
            should_finalize = True
            if new_status == "Valid":
                finalization_reason = "Case determined as not fruitless and wasteful"
            elif new_status == "Recovered":
                finalization_reason = "Case recovered by Loss Control Committee"
            elif new_status == "Written Off":
                finalization_reason = "Case written off by approval"

        # fy_id validation moved to before workflow transitions

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

        conn.commit()
        conn.close()

        # Log the workflow change after connection is fully closed
        if update_fields:
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

        return True

    except Exception as e:
        print(f"Error in handle_case_status_change: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def copy_case_to_recovered(case_id, transaction_no, user_id=None):
    """
    Copy a case to Recovered list when Loss Control status becomes Recovered

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """
    print(f"DEBUG: copy_case_to_recovered called for case_id: {case_id}, transaction_no: {transaction_no}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the current case data
        cursor.execute("""
            SELECT * FROM cases WHERE id = ?
        """, (case_id,))

        case_data = cursor.fetchone()
        if not case_data:
            print(f"DEBUG: Case {case_id} not found for copying")
            return False

        # Get column names
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        # Create dictionary from case data
        case_dict = dict(zip(columns, case_data))
        print(f"DEBUG: Original case fy_id: {case_dict.get('fy_id')}")

        # Modify the case data for the Recovered copy
        case_dict['list'] = 'Recovered'
        case_dict['status'] = 'Recovered'
        case_dict['loss_control_recommendation'] = 'Recovered'  # Set Loss Control status for copied case
        case_dict['original_list'] = case_dict.get('list', 'Lead Schedule')
        case_dict['is_finalized'] = 1  # Recovered cases are finalized
        case_dict['finalized_date'] = datetime.now().strftime("%Y-%m-%d")
        case_dict['finalization_reason'] = 'Case recovered by Loss Control Committee'

        # Extract base transaction_no (remove any existing suffixes)
        base_transaction_no = transaction_no
        if "-LS" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-LS", "")
        elif "-WOR" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-WOR", "")
        elif "-REC" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-REC", "")

        # Modify transaction_no to avoid unique constraint (add -REC suffix)
        case_dict['transaction_no'] = f"{base_transaction_no}-REC"

        # CRITICAL FIX: Ensure fy_id is valid
        original_fy_id = case_dict.get('fy_id')
        if original_fy_id is None or original_fy_id not in [fy[0] for fy in cursor.execute("SELECT id FROM financial_years").fetchall()]:
            print(f"DEBUG: Invalid fy_id {original_fy_id} detected for case {transaction_no}")
            # Get current financial year ID
            from scripts.Utilities.financial_utils import get_current_open_financial_year
            current_fy = get_current_open_financial_year()
            if current_fy:
                case_dict['fy_id'] = current_fy[0]
                print(f"DEBUG: Fixed invalid fy_id for case {transaction_no}: {original_fy_id} -> {current_fy[0]}")
            else:
                print(f"ERROR: Cannot copy case {transaction_no} - no open financial year found")
                return False

        # Remove the id field for INSERT
        case_dict.pop('id', None)

        # Check if case already exists in Recovered
        cursor.execute("""
            SELECT id FROM cases WHERE transaction_no = ? AND list = 'Recovered'
        """, (f"{transaction_no}-REC",))

        existing_case = cursor.fetchone()
        if existing_case:
            print(f"DEBUG: Case {transaction_no} already exists in Recovered (ID: {existing_case[0]})")
            # Update the original case Loss Control status
            cursor.execute("""
                UPDATE cases SET loss_control_recommendation = ? WHERE id = ?
            """, ('Recovered', case_id))
            conn.commit()
            return True  # Consider this a success since the case is already there

        print(f"DEBUG: Inserting copied case with fy_id: {case_dict.get('fy_id')}")

        # Insert the copied case
        columns_str = ', '.join(case_dict.keys())
        placeholders = ', '.join(['?' for _ in case_dict])
        values = list(case_dict.values())

        cursor.execute(f"""
            INSERT INTO cases ({columns_str}) VALUES ({placeholders})
        """, values)

        new_case_id = cursor.lastrowid
        print(f"DEBUG: Copied case inserted with new ID: {new_case_id}")

        # Update the original case Loss Control status
        cursor.execute("""
            UPDATE cases SET loss_control_recommendation = ? WHERE id = ?
        """, ('Recovered', case_id))

        conn.commit()
        print(f"DEBUG: Case copying completed successfully for {transaction_no}")

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "transaction_no": transaction_no,
            "action": "copied_to_recovered",
            "new_case_id": new_case_id,
            "user_id": user_id
        }

        save_audit_log("case_copied", workflow_data, get_financial_year())

        return True

    except Exception as e:
        print(f"Error copying case to Recovered: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


def copy_case_to_write_off_recommended_from_lead_schedule(case_id, transaction_no, user_id=None):
    """
    Copy a case from Lead Schedule to Write-Off Recommended when Loss Control status becomes Write Off Recommended

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """
    print(f"DEBUG: copy_case_to_write_off_recommended_from_lead_schedule called for case_id: {case_id}, transaction_no: {transaction_no}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the current case data
        cursor.execute("""
            SELECT * FROM cases WHERE id = ?
        """, (case_id,))

        case_data = cursor.fetchone()
        if not case_data:
            print(f"DEBUG: Case {case_id} not found for copying")
            return False

        # Get column names
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        # Create dictionary from case data
        case_dict = dict(zip(columns, case_data))
        print(f"DEBUG: Original case fy_id: {case_dict.get('fy_id')}")

        # Modify the case data for the Write-Off Recommended copy
        case_dict['list'] = 'Write-Off Recommended'
        case_dict['status'] = 'Write Off Recommended'
        case_dict['loss_control_recommendation'] = 'Write Off Recommended'  # Set Loss Control status for copied case
        case_dict['original_list'] = case_dict.get('list', 'Lead Schedule')
        case_dict['is_finalized'] = 0  # Write-Off Recommended cases are not yet finalized
        case_dict['finalized_date'] = None
        case_dict['finalization_reason'] = None

        # Extract base transaction_no (remove any existing suffixes)
        base_transaction_no = transaction_no
        if "-LS" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-LS", "")
        elif "-WOR" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-WOR", "")
        elif "-REC" in base_transaction_no:
            base_transaction_no = base_transaction_no.replace("-REC", "")

        # Modify transaction_no to avoid unique constraint (add -WOR suffix)
        case_dict['transaction_no'] = f"{base_transaction_no}-WOR"

        # CRITICAL FIX: Ensure fy_id is valid
        original_fy_id = case_dict.get('fy_id')
        if original_fy_id is None or original_fy_id not in [fy[0] for fy in cursor.execute("SELECT id FROM financial_years").fetchall()]:
            print(f"DEBUG: Invalid fy_id {original_fy_id} detected for case {transaction_no}")
            # Get current financial year ID
            from scripts.Utilities.financial_utils import get_current_open_financial_year
            current_fy = get_current_open_financial_year()
            if current_fy:
                case_dict['fy_id'] = current_fy[0]
                print(f"DEBUG: Fixed invalid fy_id for case {transaction_no}: {original_fy_id} -> {current_fy[0]}")
            else:
                print(f"ERROR: Cannot copy case {transaction_no} - no open financial year found")
                return False

        # Remove the id field for INSERT
        case_dict.pop('id', None)

        # Check if case already exists in Write-Off Recommended
        cursor.execute("""
            SELECT id FROM cases WHERE transaction_no = ? AND list = 'Write-Off Recommended'
        """, (f"{transaction_no}-WOR",))

        existing_case = cursor.fetchone()
        if existing_case:
            print(f"DEBUG: Case {transaction_no} already exists in Write-Off Recommended (ID: {existing_case[0]})")
            # Update the original case Loss Control status
            cursor.execute("""
                UPDATE cases SET loss_control_recommendation = ? WHERE id = ?
            """, ('Write Off Recommended', case_id))
            conn.commit()
            return True  # Consider this a success since the case is already there

        print(f"DEBUG: Inserting copied case with fy_id: {case_dict.get('fy_id')}")

        # Insert the copied case
        columns_str = ', '.join(case_dict.keys())
        placeholders = ', '.join(['?' for _ in case_dict])
        values = list(case_dict.values())

        cursor.execute(f"""
            INSERT INTO cases ({columns_str}) VALUES ({placeholders})
        """, values)

        new_case_id = cursor.lastrowid
        print(f"DEBUG: Copied case inserted with new ID: {new_case_id}")

        # Update the original case Loss Control status
        cursor.execute("""
            UPDATE cases SET loss_control_recommendation = ? WHERE id = ?
        """, ('Write Off Recommended', case_id))

        conn.commit()
        print(f"DEBUG: Case copying completed successfully for {transaction_no}")

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "transaction_no": transaction_no,
            "action": "copied_to_write_off_recommended",
            "new_case_id": new_case_id,
            "user_id": user_id
        }

        save_audit_log("case_copied", workflow_data, get_financial_year())

        return True

    except Exception as e:
        print(f"Error copying case to Write-Off Recommended: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


def copy_case_to_write_off_recommended(case_id, transaction_no, user_id=None):
    """
    Copy a case from Lead Schedule to Write-Off Recommended when status becomes Write Off Recommended

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """
    print(f"DEBUG: copy_case_to_write_off_recommended called for case_id: {case_id}, transaction_no: {transaction_no}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the current case data
        cursor.execute("""
            SELECT * FROM cases WHERE id = ?
        """, (case_id,))

        case_data = cursor.fetchone()
        if not case_data:
            print(f"DEBUG: Case {case_id} not found for copying")
            return False

        # Get column names
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        # Create dictionary from case data
        case_dict = dict(zip(columns, case_data))
        print(f"DEBUG: Original case fy_id: {case_dict.get('fy_id')}")

        # Modify the case data for the Write-Off Recommended copy
        case_dict['list'] = 'Write-Off Recommended'
        case_dict['status'] = 'Write Off Recommended'
        case_dict['original_list'] = 'Lead Schedule'
        case_dict['is_finalized'] = 0
        case_dict['finalized_date'] = None
        case_dict['finalization_reason'] = None

        # Modify transaction_no to avoid unique constraint (add -WOR suffix)
        case_dict['transaction_no'] = f"{transaction_no}-WOR"

        # CRITICAL FIX: Ensure fy_id is valid
        original_fy_id = case_dict.get('fy_id')
        if original_fy_id is None or original_fy_id not in [fy[0] for fy in cursor.execute("SELECT id FROM financial_years").fetchall()]:
            print(f"DEBUG: Invalid fy_id {original_fy_id} detected for case {transaction_no}")
            # Get current financial year ID
            from scripts.Utilities.financial_utils import get_current_open_financial_year
            current_fy = get_current_open_financial_year()
            if current_fy:
                case_dict['fy_id'] = current_fy[0]
                print(f"DEBUG: Fixed invalid fy_id for case {transaction_no}: {original_fy_id} -> {current_fy[0]}")
            else:
                print(f"ERROR: Cannot copy case {transaction_no} - no open financial year found")
                return False

        # Remove the id field for INSERT
        case_dict.pop('id', None)

        # Check if case already exists in Write-Off Recommended
        cursor.execute("""
            SELECT id FROM cases WHERE transaction_no = ? AND list = 'Write-Off Recommended'
        """, (f"{transaction_no}-WOR",))

        existing_case = cursor.fetchone()
        if existing_case:
            print(f"DEBUG: Case {transaction_no} already exists in Write-Off Recommended (ID: {existing_case[0]})")
            # Update the original case status to Write Off (stays in Lead Schedule)
            cursor.execute("""
                UPDATE cases SET status = ?, loss_control_recommendation = ? WHERE id = ?
            """, ('Write Off', 'Write Off', case_id))
            conn.commit()
            return True  # Consider this a success since the case is already there

        print(f"DEBUG: Inserting copied case with fy_id: {case_dict.get('fy_id')}")

        # Insert the copied case
        columns_str = ', '.join(case_dict.keys())
        placeholders = ', '.join(['?' for _ in case_dict])
        values = list(case_dict.values())

        cursor.execute(f"""
            INSERT INTO cases ({columns_str}) VALUES ({placeholders})
        """, values)

        new_case_id = cursor.lastrowid
        print(f"DEBUG: Copied case inserted with new ID: {new_case_id}")

        # Update the original case status to Write Off (stays in Lead Schedule)
        cursor.execute("""
            UPDATE cases SET status = ?, loss_control_recommendation = ? WHERE id = ?
        """, ('Write Off', 'Write Off', case_id))

        conn.commit()
        print(f"DEBUG: Case copying completed successfully for {transaction_no}")

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "transaction_no": transaction_no,
            "action": "copied_to_write_off_recommended",
            "new_case_id": new_case_id,
            "user_id": user_id
        }

        save_audit_log("case_copied", workflow_data, get_financial_year())

        return True

    except Exception as e:
        print(f"Error copying case to Write-Off Recommended: {e}")
        import traceback
        traceback.print_exc()
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


def copy_case_to_lead_schedule(case_id, transaction_no, user_id=None):
    """
    Copy a case from Checklist to Lead Schedule when status becomes Confirmed

    Args:
        case_id: Database ID of the case
        transaction_no: Transaction number of the case
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """
    print(f"DEBUG: copy_case_to_lead_schedule called for case_id: {case_id}, transaction_no: {transaction_no}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the current case data
        cursor.execute("""
            SELECT * FROM cases WHERE id = ?
        """, (case_id,))

        case_data = cursor.fetchone()
        if not case_data:
            print(f"DEBUG: Case {case_id} not found for copying")
            return False

        # Get column names
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        # Create dictionary from case data
        case_dict = dict(zip(columns, case_data))
        print(f"DEBUG: Original case fy_id: {case_dict.get('fy_id')}")

        # Modify the case data for the Lead Schedule copy
        case_dict['list'] = 'Lead Schedule'
        case_dict['status'] = 'Awaiting LC determination'
        case_dict['original_list'] = 'Checklist'
        case_dict['is_finalized'] = 0
        case_dict['finalized_date'] = None
        case_dict['finalization_reason'] = None

        # Modify transaction_no to avoid unique constraint (add -LS suffix)
        case_dict['transaction_no'] = f"{transaction_no}-LS"

        # CRITICAL FIX: Ensure fy_id is valid
        original_fy_id = case_dict.get('fy_id')
        if original_fy_id is None or original_fy_id not in [fy[0] for fy in cursor.execute("SELECT id FROM financial_years").fetchall()]:
            print(f"DEBUG: Invalid fy_id {original_fy_id} detected for case {transaction_no}")
            # Get current financial year ID
            from scripts.Utilities.financial_utils import get_current_open_financial_year
            current_fy = get_current_open_financial_year()
            if current_fy:
                case_dict['fy_id'] = current_fy[0]
                print(f"DEBUG: Fixed invalid fy_id for case {transaction_no}: {original_fy_id} -> {current_fy[0]}")
            else:
                print(f"ERROR: Cannot copy case {transaction_no} - no open financial year found")
                return False

        # Remove the id field for INSERT
        case_dict.pop('id', None)

        # Check if case already exists in Lead Schedule
        cursor.execute("""
            SELECT id FROM cases WHERE transaction_no = ? AND list = 'Lead Schedule'
        """, (f"{transaction_no}-LS",))

        existing_case = cursor.fetchone()
        if existing_case:
            print(f"DEBUG: Case {transaction_no} already exists in Lead Schedule (ID: {existing_case[0]})")
            # Update the original case status to Confirmed
            cursor.execute("""
                UPDATE cases SET status = ? WHERE id = ?
            """, ('Confirmed', case_id))
            conn.commit()
            return True  # Consider this a success since the case is already there

        print(f"DEBUG: Inserting copied case with fy_id: {case_dict.get('fy_id')}")

        # Insert the copied case
        columns_str = ', '.join(case_dict.keys())
        placeholders = ', '.join(['?' for _ in case_dict])
        values = list(case_dict.values())

        cursor.execute(f"""
            INSERT INTO cases ({columns_str}) VALUES ({placeholders})
        """, values)

        new_case_id = cursor.lastrowid
        print(f"DEBUG: Copied case inserted with new ID: {new_case_id}")

        # Update the original case status to Confirmed
        cursor.execute("""
            UPDATE cases SET status = ? WHERE id = ?
        """, ('Confirmed', case_id))

        conn.commit()
        print(f"DEBUG: Case copying completed successfully for {transaction_no}")

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "transaction_no": transaction_no,
            "action": "copied_to_lead_schedule",
            "new_case_id": new_case_id,
            "user_id": user_id
        }

        save_audit_log("case_copied", workflow_data, get_financial_year())

        return True

    except Exception as e:
        print(f"Error copying case to Lead Schedule: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()