import json
import sqlite3
from datetime import datetime

from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year


def handle_loss_control_status_change(
    case_id, base_transaction_no, loss_control_status, user_id=None
):
    """
    Handle Loss Control status changes in the single-case model.

    This function manages LC Committee determinations for Confirmed cases:
    - "Recovered": Case gets -REC suffix, finalized, appears in Recovered list
    - "Write-Off Recommended": Case gets -WOR suffix, appears in Write-Off Recommended list

    Both statuses require evidence uploads and LC minutes.

    Args:
        case_id: Database ID of the case
        base_transaction_no: Base transaction number (without suffixes)
        loss_control_status: New Loss Control status ("Recovered" or "Write-Off Recommended")
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """

    print(
        f"DEBUG: handle_loss_control_status_change called for case_id: {case_id}, base_transaction_no: {base_transaction_no}, loss_control_status: {loss_control_status}"
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current case data
        cursor.execute(
            "SELECT assessment_status, lc_status, suffixes, is_finalized FROM cases WHERE id = ?",
            (case_id,),
        )
        current_data = cursor.fetchone()

        if not current_data:
            print(f"DEBUG: Case {case_id} not found")
            return False

        assessment_status, current_lc_status, current_suffixes, is_finalized = (
            current_data
        )
        print(
            f"DEBUG: Case {case_id} assessment_status: {assessment_status}, lc_status: {current_lc_status}, suffixes: {current_suffixes}"
        )

        # Prevent changes to finalized cases
        if is_finalized:
            return False

        # Validate that case is in Confirmed status
        if assessment_status != "Confirmed":
            print(
                f"ERROR: Cannot change LC status for case not in Confirmed assessment status"
            )
            return False

        # Check if evidence is uploaded for LC status changes
        cursor.execute("SELECT evidence_paths FROM cases WHERE id = ?", (case_id,))
        evidence_data = cursor.fetchone()
        if evidence_data and evidence_data[0]:
            try:
                evidence_dict = json.loads(evidence_data[0])
                if not evidence_dict or not any(evidence_dict.values()):
                    print(f"ERROR: Evidence must be uploaded before changing LC status")
                    return False
            except json.JSONDecodeError:
                print(f"ERROR: Invalid evidence data format")
                return False
        else:
            print(f"ERROR: Evidence must be uploaded before changing LC status")
            return False

        # Parse current suffixes
        suffixes = current_suffixes.split(",") if current_suffixes else []

        # Update based on new LC status
        if loss_control_status == "Recovery in Progress":
            new_lc_status = "Recovery in Progress"
            # Add -RIP suffix if not present (Recovery In Progress)
            if "-RIP" not in suffixes:
                suffixes.append("-RIP")
            # Remove conflicting suffixes
            suffixes = [s for s in suffixes if s not in ["-REC", "-WOR", "-WO"]]
            is_finalized = False
            
        elif loss_control_status == "Recovered":
            new_lc_status = "Recovered"
            # Add -REC suffix if not present
            if "-REC" not in suffixes:
                suffixes.append("-REC")
            # Remove conflicting suffixes
            suffixes = [s for s in suffixes if s not in ["-RIP", "-WOR", "-WO"]]
            is_finalized = True
            finalization_reason = "Case recovered by Loss Control Committee"

        elif loss_control_status in ["Write Off Recommended", "Write-Off Recommended"]:
            new_lc_status = "Write-Off Recommended"
            # Add -WOR suffix if not present
            if "-WOR" not in suffixes:
                suffixes.append("-WOR")
            # Remove conflicting suffixes
            suffixes = [s for s in suffixes if s not in ["-RIP", "-REC", "-WO"]]
            is_finalized = False

        else:
            print(f"ERROR: Invalid loss control status: {loss_control_status}")
            return False

        # Update the case
        cursor.execute(
            """
            UPDATE cases SET
                lc_status = ?,
                suffixes = ?,
                is_finalized = ?,
                finalized_date = ?,
                finalization_reason = ?
            WHERE id = ?
        """,
            (
                new_lc_status,
                ",".join(suffixes),
                1 if is_finalized else 0,
                datetime.now().strftime("%Y-%m-%d") if is_finalized else None,
                finalization_reason if is_finalized else None,
                case_id,
            ),
        )

        conn.commit()

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "base_transaction_no": base_transaction_no,
            "action": "lc_status_change",
            "previous_lc_status": current_lc_status,
            "new_lc_status": new_lc_status,
            "suffixes": ",".join(suffixes),
            "finalized": is_finalized,
            "user_id": user_id,
        }

        save_audit_log("lc_status_change", workflow_data, get_financial_year())

        print(f"DEBUG: LC status change completed for case {base_transaction_no}")
        return True

    except Exception as e:
        print(f"Error in handle_loss_control_status_change: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def handle_case_status_change(
    case_id, base_transaction_no, new_assessment_status, user_id=None
):
    """
    Handle assessment status changes in the single-case model.

    This function manages the workflow transitions for case assessment statuses:
    - "Alleged" -> "Under Assessment" -> "Valid" (finalized, not F&W)
    - "Alleged" -> "Under Assessment" -> "Confirmed" -> LC determination

    For "Valid": Case is finalized as not fruitless/wasteful
    For "Confirmed": Case gets -LS suffix and appears in Lead Schedule for LC review

    Args:
        case_id: Database ID of the case
        base_transaction_no: Base transaction number (without suffixes)
        new_assessment_status: New assessment status ("Alleged", "Under Assessment", "Valid", "Confirmed")
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """

    print(
        f"DEBUG: handle_case_status_change called for case_id: {case_id}, base_transaction_no: {base_transaction_no}, new_assessment_status: {new_assessment_status}"
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current case data
        cursor.execute(
            "SELECT assessment_status, lc_status, suffixes, is_finalized FROM cases WHERE id = ?",
            (case_id,),
        )
        current_data = cursor.fetchone()

        if not current_data:
            print(f"DEBUG: Case {case_id} not found")
            return False

        current_assessment_status, current_lc_status, current_suffixes, is_finalized = (
            current_data
        )
        print(
            f"DEBUG: Case {case_id} current assessment_status: {current_assessment_status}, lc_status: {current_lc_status}, suffixes: {current_suffixes}"
        )

        # Prevent changes to finalized cases (except for Valid->Confirmed edge case)
        if is_finalized and new_assessment_status != "Confirmed":
            return False

        # Parse current suffixes
        suffixes = current_suffixes.split(",") if current_suffixes else []

        # Handle status transitions
        if new_assessment_status == "Valid":
            # Check if evidence is uploaded before marking as Valid
            cursor.execute("SELECT evidence_paths FROM cases WHERE id = ?", (case_id,))
            evidence_data = cursor.fetchone()
            if evidence_data and evidence_data[0]:
                try:
                    evidence_dict = json.loads(evidence_data[0])
                    if not evidence_dict or not any(evidence_dict.values()):
                        print(
                            f"ERROR: Assessment evidence must be uploaded before marking case as Valid"
                        )
                        return False
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid evidence data format")
                    return False
            else:
                print(
                    f"ERROR: Assessment evidence must be uploaded before marking case as Valid"
                )
                return False

            # Case is not F&W, finalize it
            is_finalized = True
            finalization_reason = "Case determined as not fruitless and wasteful"
            # Remove any LC-related suffixes
            suffixes = [s for s in suffixes if s not in ["-LS", "-REC", "-WOR", "-WO"]]

        elif new_assessment_status == "Confirmed":
            # Check if evidence is uploaded before marking as Confirmed
            cursor.execute("SELECT evidence_paths FROM cases WHERE id = ?", (case_id,))
            evidence_data = cursor.fetchone()
            if evidence_data and evidence_data[0]:
                try:
                    evidence_dict = json.loads(evidence_data[0])
                    if not evidence_dict or not any(evidence_dict.values()):
                        print(
                            f"ERROR: Assessment evidence must be uploaded before marking case as Confirmed"
                        )
                        return False
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid evidence data format")
                    return False
            else:
                print(
                    f"ERROR: Assessment evidence must be uploaded before marking case as Confirmed"
                )
                return False

            # Case is F&W, add -LS suffix to appear in Lead Schedule
            if "-LS" not in suffixes:
                suffixes.append("-LS")
            # Reset LC status only if not already set
            if current_lc_status in (None, "Awaiting LC determination"):
                current_lc_status = "Awaiting LC determination"
            is_finalized = False
            finalization_reason = None

        elif new_assessment_status in ["Alleged", "Under Assessment"]:
            # Reset to initial states
            suffixes = [s for s in suffixes if s not in ["-LS", "-REC", "-WOR", "-WO"]]
            current_lc_status = None
            is_finalized = False
            finalization_reason = None

        else:
            print(f"ERROR: Invalid assessment status: {new_assessment_status}")
            return False

        # Update the case
        cursor.execute(
            """
            UPDATE cases SET
                assessment_status = ?,
                lc_status = ?,
                suffixes = ?,
                is_finalized = ?,
                finalized_date = ?,
                finalization_reason = ?
            WHERE id = ?
        """,
            (
                new_assessment_status,
                current_lc_status,
                ",".join(suffixes),
                1 if is_finalized else 0,
                datetime.now().strftime("%Y-%m-%d") if is_finalized else None,
                finalization_reason if is_finalized else None,
                case_id,
            ),
        )

        conn.commit()

        # Log the workflow change
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "base_transaction_no": base_transaction_no,
            "action": "assessment_status_change",
            "previous_assessment_status": current_assessment_status,
            "new_assessment_status": new_assessment_status,
            "lc_status": current_lc_status,
            "suffixes": ",".join(suffixes),
            "finalized": is_finalized,
            "user_id": user_id,
        }

        save_audit_log("assessment_status_change", workflow_data, get_financial_year())

        print(
            f"DEBUG: Assessment status change completed for case {base_transaction_no}"
        )
        return True

    except Exception as e:
        print(f"Error in handle_case_status_change: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def approve_write_off_submission(write_off_group_id, user_id=None):
    """
    Approve a write-off submission, updating all cases in the group to Written Off status.

    Args:
        write_off_group_id: The group ID of cases to write off (e.g., "202600001-WOA")
        user_id: User making the change (optional)

    Returns:
        bool: Success status
    """

    print(f"DEBUG: approve_write_off_submission called for group: {write_off_group_id}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get all cases in the group
        cursor.execute(
            """
            SELECT id, base_transaction_no, suffixes
            FROM cases
            WHERE write_off_group_id = ? AND lc_status = 'Write-Off Recommended'
        """,
            (write_off_group_id,),
        )

        cases_to_update = cursor.fetchall()
        if not cases_to_update:
            print(f"DEBUG: No cases found in group {write_off_group_id}")
            return False

        print(f"DEBUG: Found {len(cases_to_update)} cases to write off")

        # Update each case
        for case_id, base_transaction_no, suffixes in cases_to_update:
            # Parse and update suffixes
            suffix_list = suffixes.split(",") if suffixes else []
            if "-WO" not in suffix_list:
                suffix_list.append("-WO")
            # Remove -WOR since it's now approved
            suffix_list = [s for s in suffix_list if s != "-WOR"]

            cursor.execute(
                """
                UPDATE cases SET
                    lc_status = 'Written Off',
                    suffixes = ?,
                    is_finalized = 1,
                    finalized_date = ?,
                    finalization_reason = ?
                WHERE id = ?
            """,
                (
                    ",".join(suffix_list),
                    datetime.now().strftime("%Y-%m-%d"),
                    "Case written off by approval",
                    case_id,
                ),
            )

        conn.commit()

        # Log the approval
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "write_off_group_id": write_off_group_id,
            "cases_written_off": len(cases_to_update),
            "case_ids": [case[0] for case in cases_to_update],
            "user_id": user_id,
        }

        save_audit_log("write_off_approved", workflow_data, get_financial_year())

        print(f"DEBUG: Write-off approval completed for group {write_off_group_id}")
        return True

    except Exception as e:
        print(f"Error approving write-off submission: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def create_write_off_group(selected_case_ids, user_id=None):
    """
    Create a write-off group from selected cases in Write-Off Recommended list.

    Args:
        selected_case_ids: List of case IDs to group
        user_id: User making the change (optional)

    Returns:
        str: The group ID created (e.g., "202600001-WOA")
    """

    if not selected_case_ids:
        return None

    print(f"DEBUG: create_write_off_group called for {len(selected_case_ids)} cases")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the base transaction number from the first case
        cursor.execute(
            "SELECT base_transaction_no FROM cases WHERE id = ?",
            (selected_case_ids[0],),
        )
        result = cursor.fetchone()
        if not result:
            return None

        base_no = result[0]
        group_id = f"{base_no}-WOA"

        # Update all selected cases with the group ID
        for case_id in selected_case_ids:
            cursor.execute(
                """
                UPDATE cases SET write_off_group_id = ? WHERE id = ?
            """,
                (group_id, case_id),
            )

        conn.commit()

        # Log the grouping
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "write_off_group_id": group_id,
            "cases_grouped": len(selected_case_ids),
            "case_ids": selected_case_ids,
            "user_id": user_id,
        }

        save_audit_log("write_off_group_created", workflow_data, get_financial_year())

        print(f"DEBUG: Write-off group {group_id} created successfully")
        return group_id

    except Exception as e:
        print(f"Error creating write-off group: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_case_workflow_status(case_id):
    """
    Get comprehensive workflow status for a case in the single-case model

    Returns:
        dict: Workflow status information
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT base_transaction_no, assessment_status, lc_status, suffixes,
                   is_finalized, finalized_date, write_off_group_id
            FROM cases
            WHERE id = ?
        """,
            (case_id,),
        )

        result = cursor.fetchone()
        if result:
            (
                base_transaction_no,
                assessment_status,
                lc_status,
                suffixes,
                is_finalized,
                finalized_date,
                write_off_group_id,
            ) = result

            # Parse suffixes
            suffix_list = suffixes.split(",") if suffixes else []

            # Determine which lists this case appears in
            appears_in = ["Checklist"]  # All cases appear in checklist

            if "-LS" in suffix_list and assessment_status == "Confirmed":
                appears_in.append("Lead Schedule")
            if "-REC" in suffix_list:
                appears_in.append("Recovered")
            if "-WOR" in suffix_list:
                appears_in.append("Write-Off Recommended")
            if "-WO" in suffix_list:
                appears_in.append("Written Off")

            return {
                "base_transaction_no": base_transaction_no,
                "assessment_status": assessment_status,
                "lc_status": lc_status,
                "suffixes": suffix_list,
                "appears_in_lists": appears_in,
                "is_finalized": bool(is_finalized),
                "finalized_date": finalized_date,
                "write_off_group_id": write_off_group_id,
                "can_edit": not bool(is_finalized),
                "can_change_assessment_status": assessment_status
                in ["Alleged", "Under Assessment"],
                "can_change_lc_status": assessment_status == "Confirmed"
                and not is_finalized,
                "needs_evidence": (
                    assessment_status in ["Valid", "Confirmed"]
                    or lc_status in ["Recovered", "Write Off Recommended"]
                ),
            }

        return None

    except Exception as e:
        print(f"Error getting case workflow status: {e}")
        return None
    finally:
        conn.close()


def check_workflow_completion():
    """
    Check for cases that need workflow attention in the single-case model
    Returns list of cases needing action
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Cases in Lead Schedule (Confirmed + -LS) that need LC determination
        cursor.execute(
            """
            SELECT base_transaction_no, assessment_status, lc_status
            FROM cases
            WHERE assessment_status = 'Confirmed'
            AND (suffixes LIKE '%-LS%' OR lc_status IS NULL)
            AND lc_status = 'Awaiting LC determination'
            AND is_finalized = 0
        """
        )

        needs_lc_determination = cursor.fetchall()

        # Cases recommended for write-off that need grouping/submission
        cursor.execute(
            """
            SELECT base_transaction_no, assessment_status, lc_status
            FROM cases
            WHERE lc_status = 'Write-Off Recommended'
            AND write_off_group_id IS NULL
            AND is_finalized = 0
        """
        )

        needs_write_off_grouping = cursor.fetchall()

        return {
            "needs_lc_determination": needs_lc_determination,
            "needs_write_off_grouping": needs_write_off_grouping,
        }

    except Exception as e:
        print(f"Error checking workflow completion: {e}")
        return {"needs_lc_determination": [], "needs_write_off_grouping": []}
    finally:
        conn.close()


def get_list_filter_query(list_name):
    """
    Get the SQL WHERE clause for filtering cases by list in the single-case model

    Args:
        list_name: Name of the list ("Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off")

    Returns:
        str: SQL WHERE clause
    """
    from scripts.Utilities.shared_case_filter_utils import get_list_filter_conditions
    
    return get_list_filter_conditions(list_name)


def get_display_transaction_no(base_transaction_no, suffixes):
    """
    Generate the display transaction number including appropriate suffixes

    Args:
        base_transaction_no: Base transaction number
        suffixes: Comma-separated list of suffixes

    Returns:
        str: Display transaction number
    """
    if not suffixes:
        return base_transaction_no

    suffix_list = suffixes.split(",")
    # Return the most relevant suffix for display
    if "-WO" in suffix_list:
        return f"{base_transaction_no}-WO"
    elif "-REC" in suffix_list:
        return f"{base_transaction_no}-REC"
    elif "-WOR" in suffix_list:
        return f"{base_transaction_no}-WOR"
    elif "-LS" in suffix_list:
        return f"{base_transaction_no}-LS"
    else:
        return base_transaction_no
