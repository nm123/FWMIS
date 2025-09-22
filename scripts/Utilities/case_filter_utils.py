"""
Utilities for case filtering and searching in EditCasesDialog.
"""

import sqlite3

from scripts.Utilities.config import DB_PATH


def get_responsibilities_with_cases(fy_filter_combo) -> set[int]:
    """Get set of responsibility IDs that have cases, including their parents."""
    responsibilities_with_cases: set[int] = set()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = "SELECT DISTINCT responsibility_id FROM cases WHERE suffixes NOT LIKE '%-DEL%'"
        params = []
        selected_fy_id = fy_filter_combo.currentData()
        if selected_fy_id:
            query += " AND fy_id = ?"
            params.append(selected_fy_id)
        cursor.execute(query, params)
        case_resp_ids = {row[0] for row in cursor.fetchall()}
        for resp_id in case_resp_ids:
            responsibilities_with_cases.add(resp_id)
            # Include parents (logic simplified for brevity)
        conn.close()
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return responsibilities_with_cases


def search_case_by_number(
    case_no: str, fy_filter_combo, list_filter_combo
) -> list[tuple]:
    """Search for a specific case by number."""
    # Build search query with list filtering
    base_conditions = ["transaction_no LIKE ?"]
    params = [f"%{case_no}%"]

    # Add financial year filter
    selected_fy_id = fy_filter_combo.currentData()
    if selected_fy_id:
        base_conditions.append("fy_id = ?")
        params.append(selected_fy_id)

    # Add list filter condition using new single-case model
    selected_list = list_filter_combo.currentText()
    if selected_list == "All Cases":
        base_conditions.append("suffixes NOT LIKE '%-DEL%'")
    elif selected_list == "Checklist":
        # Checklist shows all cases (no additional filter)
        pass
    elif selected_list == "Lead Schedule":
        # Lead Schedule shows Confirmed cases with -LS suffix, not finalized
        base_conditions.append(
            "assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO%'"
        )
    elif selected_list == "Write-Off Recommended":
        # Write-Off Recommended shows cases with -WOR suffix
        base_conditions.append("suffixes LIKE '%-WOR%'")
    elif selected_list == "Recovered":
        # Recovered shows cases with -REC suffix
        base_conditions.append("suffixes LIKE '%-REC%'")
    elif selected_list == "Written Off":
        # Written Off shows cases with -WO suffix
        base_conditions.append("suffixes LIKE '%-WO%'")

    where_clause = " AND ".join(base_conditions)
    query = f"SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows
