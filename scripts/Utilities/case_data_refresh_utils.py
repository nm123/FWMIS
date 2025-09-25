"""
Utilities for refreshing case data in EditCasesDialog.
"""

import sqlite3

from scripts.case_management_modules.case_table_utils import \
    populate_case_table, create_totals_widget
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
    except Exception as e:
        print(f"DEBUG: Error in refresh_cases setup: {e}")
        import traceback

        traceback.print_exc()
        dialog_instance.refresh_in_progress = False
        return

    # Use shared filtering logic for consistency
    from scripts.Utilities.shared_case_filter_utils import build_case_query, execute_case_query
    
    # Build consistent query using shared filtering logic
    query, params = build_case_query(dialog_instance.fy_filter_combo, dialog_instance.list_filter_combo, resp_ids)
    print(f"DEBUG: Executing query: {query}")
    print(f"DEBUG: Query params: {params}")

    try:
        rows = execute_case_query(query, params)
        print(f"DEBUG: Retrieved {len(rows)} rows from database")
        selected_list = dialog_instance.list_filter_combo.currentText()
        populate_case_table(
            dialog_instance.case_table,
            rows,
            selected_list,
            include_edit=True,
            edit_callback=dialog_instance.edit_case_by_row,
        )
        
        # Update totals widget
        if hasattr(dialog_instance, 'totals_widget'):
            # Get financial year ID for totals calculation
            fy_id = dialog_instance.fy_filter_combo.currentData()
            new_totals_widget = create_totals_widget(selected_list, fy_id)
            
            # Replace the old totals widget
            layout = dialog_instance.totals_widget.parent().layout()
            layout.removeWidget(dialog_instance.totals_widget)
            dialog_instance.totals_widget.setParent(None)  # Remove from parent
            dialog_instance.totals_widget.deleteLater()
            dialog_instance.totals_widget = new_totals_widget
            layout.addWidget(dialog_instance.totals_widget)
            
    except Exception as e:
        print(f"DEBUG: Error in database query or row processing: {e}")
        import traceback

        traceback.print_exc()
        dialog_instance.refresh_in_progress = False
        return

    print("DEBUG: refresh_cases completed successfully")
    dialog_instance.refresh_in_progress = False
