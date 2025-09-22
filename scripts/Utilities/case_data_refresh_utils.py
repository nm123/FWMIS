"""
Utilities for refreshing case data in EditCasesDialog.
"""

import sqlite3

from scripts.case_management_modules.case_table_utils import \
    populate_case_table
from scripts.Utilities.config import DB_PATH


def refresh_cases(dialog_instance, resp_ids=None) -> None:
    """Refresh the cases table with filters."""
    if dialog_instance.refresh_in_progress:
        print("DEBUG: refresh_cases already in progress, skipping")
        return

    print("DEBUG: Starting refresh_cases in EditCasesDialog")
    dialog_instance.refresh_in_progress = True
    try:
        dialog_instance.case_table.setRowCount(0)
        print("DEBUG: Case table cleared")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("DEBUG: Database connection established in EditCasesDialog")
    except Exception as e:
        print(f"DEBUG: Error in refresh_cases setup: {e}")
        import traceback

        traceback.print_exc()
        dialog_instance.refresh_in_progress = False
        return

    # Build base query with list filtering
    base_conditions = []
    params = []

    # Add financial year filter
    selected_fy_id = dialog_instance.fy_filter_combo.currentData()
    if selected_fy_id:
        base_conditions.append("fy_id = ?")
        params.append(selected_fy_id)

    # Add list filter condition using new single-case model
    selected_list = dialog_instance.list_filter_combo.currentText()
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

    # Add responsibility filter if provided
    if resp_ids:
        placeholders = ",".join("?" for _ in resp_ids)
        base_conditions.append(f"responsibility_id IN ({placeholders})")
        params.extend(resp_ids)

    where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
    query = f"SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"
    print(f"DEBUG: Executing query: {query}")
    print(f"DEBUG: Query params: {params}")

    try:
        cursor.execute(query, params)
        print("DEBUG: Query executed successfully")
        rows = cursor.fetchall()
        print(f"DEBUG: Retrieved {len(rows)} rows from database")
        populate_case_table(
            dialog_instance.case_table,
            rows,
            selected_list,
            include_edit=True,
            edit_callback=dialog_instance.edit_case_by_row,
        )
    except Exception as e:
        print(f"DEBUG: Error in database query or row processing: {e}")
        import traceback

        traceback.print_exc()
        dialog_instance.refresh_in_progress = False
        return

    try:
        conn.close()
        print("DEBUG: Database connection closed in refresh_cases")
    except Exception as e:
        print(f"DEBUG: Error closing database connection: {e}")

    print("DEBUG: refresh_cases completed successfully")
    dialog_instance.refresh_in_progress = False
