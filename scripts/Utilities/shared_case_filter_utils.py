"""
Shared case filtering utilities for View Cases and Edit Cases dialogs.
Ensures identical filtering logic across both dialogs.
"""

import sqlite3

from scripts.Utilities.config import DB_PATH


def get_list_filter_conditions(selected_list):
    """
    Get SQL WHERE conditions for different list filters.
    This function ensures consistent filtering logic across View Cases and Edit Cases dialogs.

    Args:
        selected_list (str): The selected list filter ("Checklist", "Lead Schedule", etc.)

    Returns:
        str: SQL WHERE clause condition
    """
    conditions = {
        "Checklist": "1=1",  # All cases appear in Checklist
        "Lead Schedule": "assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO'",
        "Recovery in Progress": "suffixes LIKE '%-RIP%'",
        "Write-Off Recommended": "suffixes LIKE '%-WOR%'",
        "Recovered": "suffixes LIKE '%-REC%' OR EXISTS (SELECT 1 FROM installments WHERE installments.case_id = cases.id)",
        "Written Off": "suffixes LIKE '%-WO' AND suffixes NOT LIKE '%-WOR%'",
    }

    return conditions.get(selected_list, "1=1")


def build_case_query(fy_filter_combo, list_filter_combo, resp_ids=None):
    """
    Build a consistent SQL query for case filtering across both dialogs.

    Args:
        fy_filter_combo: Financial year filter combo box
        list_filter_combo: List filter combo box
        resp_ids: Optional list of responsibility IDs to filter by

    Returns:
        tuple: (query_string, params_list)
    """
    # Base conditions
    base_conditions = ["fy_id IS NOT NULL AND responsibility_id IS NOT NULL"]
    params = []

    # Add financial year filter
    selected_fy_id = fy_filter_combo.currentData()
    if selected_fy_id:
        base_conditions.append("fy_id = ?")
        params.append(selected_fy_id)

    # Add list filter condition
    selected_list = list_filter_combo.currentText()
    list_condition = get_list_filter_conditions(selected_list)
    if list_condition != "1=1":
        base_conditions.append(list_condition)

    # Add responsibility filter if provided
    if resp_ids:
        placeholders = ",".join("?" for _ in resp_ids)
        base_conditions.append(f"responsibility_id IN ({placeholders})")
        params.extend(resp_ids)

    # Build final query
    where_clause = " AND ".join(base_conditions)
    query = f"""
        SELECT transaction_no, date_reported, category, amount, assessment_status, 
               lc_status, suffixes, bas_payment_no, bas_journal_no 
        FROM cases 
        WHERE {where_clause}
        ORDER BY transaction_no
    """

    return query, params


def execute_case_query(query, params):
    """
    Execute a case query and return results.

    Args:
        query (str): SQL query string
        params (list): Query parameters

    Returns:
        list: List of case data tuples
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Database query error: {e}")
        return []
    finally:
        conn.close()


def get_responsibilities_with_cases(fy_filter_combo, list_filter_combo):
    """
    Get set of responsibility IDs that have cases for the current filters.

    Args:
        fy_filter_combo: Financial year filter combo box
        list_filter_combo: List filter combo box

    Returns:
        set: Set of responsibility IDs that have cases
    """
    responsibilities_with_cases = set()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build query with current filters
        query, params = build_case_query(fy_filter_combo, list_filter_combo)

        # Modify query to only select responsibility_id
        responsibility_query = query.replace(
            "SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no",
            "SELECT DISTINCT responsibility_id",
        )

        cursor.execute(responsibility_query, params)
        case_resp_ids = {row[0] for row in cursor.fetchall()}

        conn.close()
        return case_resp_ids

    except sqlite3.Error as e:
        print(f"Error querying responsibilities with cases: {e}")
        return set()


def search_case_by_number(case_no, fy_filter_combo, list_filter_combo):
    """
    Search for cases by number with consistent filtering.

    Args:
        case_no (str): Case number to search for (with or without FW- prefix)
        fy_filter_combo: Financial year filter combo box
        list_filter_combo: List filter combo box

    Returns:
        list: List of matching case tuples
    """
    # Normalize case number - add FW- prefix if not present
    normalized_case_no = case_no
    if not case_no.upper().startswith("FW-"):
        normalized_case_no = f"FW-{case_no}"

    # Build base query with list filtering
    base_conditions = ["(transaction_no LIKE ? OR base_transaction_no LIKE ?)"]
    base_conditions.append("fy_id IS NOT NULL AND responsibility_id IS NOT NULL")
    params = [f"%{normalized_case_no}%", f"%{normalized_case_no}%"]

    # Add financial year filter
    selected_fy_id = fy_filter_combo.currentData()
    if selected_fy_id:
        base_conditions.append("fy_id = ?")
        params.append(selected_fy_id)

    # Add list filter condition
    selected_list = list_filter_combo.currentText()
    list_condition = get_list_filter_conditions(selected_list)
    if list_condition != "1=1":
        base_conditions.append(list_condition)

    where_clause = " AND ".join(base_conditions)
    query = f"""
        SELECT transaction_no, date_reported, category, amount, assessment_status, 
               lc_status, suffixes, bas_payment_no, bas_journal_no 
        FROM cases 
        WHERE {where_clause}
    """

    return execute_case_query(query, params)
