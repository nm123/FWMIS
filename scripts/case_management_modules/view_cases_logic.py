import sqlite3
from collections import defaultdict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QTreeWidgetItem
from scripts.case_management_modules.case_table_utils import \
    populate_case_table
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.tree_utils import get_subtree_resp_ids


class ViewCasesLogic:
    @staticmethod
    def refresh_responsibilities(dialog):
        dialog.resp_tree.clear()
        resp_dict = {r["id"]: r for r in dialog.responsibilities}

        # Query database to find responsibilities with cases
        dialog.responsibilities_with_cases = (
            ViewCasesLogic.get_responsibilities_with_cases(dialog)
        )

        top_level = [r for r in dialog.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            ViewCasesLogic.add_resp_item(dialog, resp, None, resp_dict)

    @staticmethod
    def get_responsibilities_with_cases(dialog):
        """Get set of responsibility IDs that have cases, including their parents"""
        responsibilities_with_cases = set()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Build query with financial year filter (but not for "All Cases" list filter)
            query = "SELECT DISTINCT responsibility_id FROM cases WHERE list != 'Deleted Cases'"
            params = []

            # Add financial year filter if selected
            selected_fy_id = dialog.fy_filter_combo.currentData()
            if selected_fy_id:
                query += " AND fy_id = ?"
                params.append(selected_fy_id)

            cursor.execute(query, params)
            case_resp_ids = {row[0] for row in cursor.fetchall()}

            # Include parent responsibilities
            for resp_id in case_resp_ids:
                responsibilities_with_cases.add(resp_id)
                # Find and add parent IDs
                resp = next(
                    (r for r in dialog.responsibilities if r["id"] == resp_id), None
                )
                if resp and resp["parent_id"]:
                    responsibilities_with_cases.add(resp["parent_id"])

            conn.close()
        except sqlite3.Error as e:
            print(f"Error querying responsibilities with cases: {e}")

        return responsibilities_with_cases

    @staticmethod
    def add_resp_item(dialog, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])

        # Bold responsibilities that have cases
        if resp["id"] in dialog.responsibilities_with_cases:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        if parent_item is None:
            dialog.resp_tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        children = [r for r in dialog.responsibilities if r["parent_id"] == resp["id"]]
        for child in children:
            ViewCasesLogic.add_resp_item(dialog, child, item, resp_dict)

    @staticmethod
    def on_resp_select(dialog):
        selected = dialog.resp_tree.selectedItems()
        if selected:
            resp_id = selected[0].data(0, Qt.UserRole)
            subtree_ids = get_subtree_resp_ids(resp_id, dialog.responsibilities)
            ViewCasesLogic.refresh_cases(dialog, subtree_ids)
        else:
            ViewCasesLogic.refresh_cases(dialog)

    @staticmethod
    def on_case_select(dialog):
        """Highlight the responsibility in the tree when a case is selected"""
        selected_rows = set()
        for item in dialog.case_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            # Clear selection if no case is selected
            dialog.resp_tree.clearSelection()
            return

        # Get the first selected case's transaction number
        first_row = min(selected_rows)
        transaction_no = dialog.case_table.item(first_row, 0).data(Qt.UserRole)

        # Get responsibility_id for this case
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT responsibility_id FROM cases WHERE transaction_no = ?",
                (transaction_no,),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                responsibility_id = result[0]
                ViewCasesLogic.highlight_responsibility(dialog, responsibility_id)
        except sqlite3.Error as e:
            print(f"Error getting responsibility for case {transaction_no}: {e}")

    @staticmethod
    def highlight_responsibility(dialog, responsibility_id):
        """Find and highlight the responsibility in the tree"""

        def find_item_by_id(parent_item, target_id):
            """Recursively search for an item with the given ID"""
            if parent_item is None:
                # Search top-level items
                for i in range(dialog.resp_tree.topLevelItemCount()):
                    item = dialog.resp_tree.topLevelItem(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search children
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            else:
                # Search children of parent_item
                for i in range(parent_item.childCount()):
                    item = parent_item.child(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search grandchildren
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            return None

        # Find the responsibility item
        target_item = find_item_by_id(None, responsibility_id)

        if target_item:
            # Clear current selection
            dialog.resp_tree.clearSelection()
            # Select the target item
            target_item.setSelected(True)
            # Ensure it's visible
            dialog.resp_tree.scrollToItem(target_item)
            # Expand parent items to make it visible
            parent = target_item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()

    @staticmethod
    def refresh_cases(dialog, resp_ids=None):
        dialog.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build base query with list filtering
        base_conditions = ["list != 'Deleted Cases'"]
        params = []

        # Add financial year filter
        selected_fy_id = dialog.fy_filter_combo.currentData()
        if selected_fy_id:
            base_conditions.append("fy_id = ?")
            params.append(selected_fy_id)

        # Add list filter condition using new single-case model
        selected_list = dialog.list_filter_combo.currentText()
        if selected_list == "Checklist":
            # Checklist shows all cases (no additional filter)
            pass
        elif selected_list == "Lead Schedule":
            # Lead Schedule shows Confirmed cases with -LS suffix, not finalized
            base_conditions.append(
                "assessment_status = 'Confirmed' AND suffixes LIKE '%-LS%' AND suffixes NOT LIKE '%-REC%' AND suffixes NOT LIKE '%-WO%'"
            )
        elif selected_list == "Recovered":
            # Recovered shows cases with -REC suffix
            base_conditions.append("suffixes LIKE '%-REC%'")
        elif selected_list == "Write-Off Recommended":
            # Write-Off Recommended shows cases with -WOR suffix
            base_conditions.append("suffixes LIKE '%-WOR%'")
        elif selected_list == "Written Off":
            # Written Off shows cases with -WO suffix
            base_conditions.append("suffixes LIKE '%-WO%'")
        elif selected_list == "To-Do List":
            # Show both actual To-Do List cases and GJ cases with outstanding actions
            base_conditions.append(
                "(list = 'To-Do List' OR bas_journal_no IS NOT NULL)"
            )
        elif selected_list == "Deleted Cases":
            # Deleted Cases shows cases with -DEL suffix
            base_conditions.append("suffixes LIKE '%-DEL%'")

        # Add responsibility filter if provided
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            base_conditions.append(f"responsibility_id IN ({placeholders})")
            params.extend(resp_ids)

        where_clause = " AND ".join(base_conditions)
        # Select columns for shared table population (match Edit Cases query)
        query = f"SELECT transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        populate_case_table(dialog.case_table, rows, selected_list, include_edit=False)

    @staticmethod
    def show_case_details(dialog, item, selected_list=None):
        """Show detailed case information when double-clicking a case"""
        transaction_no = item.data(Qt.UserRole)
        print(f"DEBUG: Opening case: {transaction_no}")

        case_data = None
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Try to find case by transaction_no first, then fallback to case_id if transaction_no is None
        if transaction_no:
            cursor.execute(
                "SELECT * FROM cases WHERE transaction_no = ?", (transaction_no,)
            )
        else:
            # If transaction_no is None, we need to get the case_id from the table data
            # This shouldn't happen with our fallback, but just in case
            print("DEBUG: transaction_no is None, cannot open case details")
            conn.close()
            return

        case_data = cursor.fetchone()
        print(f"DEBUG: Case data found: {case_data is not None}")

        conn.close()

        if case_data:
            # Convert to dictionary for easier handling with new schema
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            case_dict = dict(zip(columns, case_data)) if columns else {}

            # Check if case is finalized
            is_finalized = case_dict.get("is_finalized", False)

            if is_finalized:
                # Show read-only details for finalized cases
                from scripts.ui.components.view_cases_ui import \
                    CaseDetailsDialog

                dialog_details = CaseDetailsDialog(case_data, dialog)
                dialog_details.exec_()
            else:
                # Open editable dialog for non-finalized cases
                from scripts.case_management_modules.edit_case_dialog import \
                    EditCaseDialog

                edit_dialog = EditCaseDialog(
                    case_dict, dialog, selected_list=selected_list
                )
                edit_dialog.case_modified.connect(
                    lambda: ViewCasesLogic.refresh_cases(dialog)
                )  # Connect refresh signal
                edit_dialog.exec_()

    @staticmethod
    def filter_responsibilities(dialog, text):
        """Filter responsibilities based on search text"""
        text = text.lower()
        if not text:
            ViewCasesLogic.refresh_responsibilities(dialog)
            return

        dialog.resp_tree.clear()

        # Find responsibilities that match the search text
        matching_resps = []
        parent_ids_to_include = set()

        for resp in dialog.responsibilities:
            if text in resp["name"].lower():
                matching_resps.append(resp)
                # Recursively collect all parent IDs up to the root
                current_parent_id = resp["parent_id"]
                while current_parent_id:
                    parent_ids_to_include.add(current_parent_id)
                    # Find the parent and get its parent_id
                    parent_resp = next(
                        (
                            r
                            for r in dialog.responsibilities
                            if r["id"] == current_parent_id
                        ),
                        None,
                    )
                    if parent_resp:
                        current_parent_id = parent_resp["parent_id"]
                    else:
                        current_parent_id = None

        # Include all parent responsibilities
        for resp in dialog.responsibilities:
            if resp["id"] in parent_ids_to_include:
                matching_resps.append(resp)

        # Remove duplicates while preserving order
        seen_ids = set()
        filtered_resps = []
        for resp in matching_resps:
            if resp["id"] not in seen_ids:
                filtered_resps.append(resp)
                seen_ids.add(resp["id"])

        # Create parent map for filtered results
        parent_map = defaultdict(list)
        for resp in filtered_resps:
            parent_map[resp["parent_id"]].append(resp)

        def add_filtered_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])

                # Bold responsibilities that have cases
                if resp["id"] in dialog.responsibilities_with_cases:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)

                if parent_id is None:
                    dialog.resp_tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        dialog.resp_tree.expandAll()

    @staticmethod
    def update_write_off_buttons_visibility(dialog):
        """Update visibility of write-off buttons based on current list filter"""
        selected_list = dialog.list_filter_combo.currentText()
        show_buttons = selected_list == "Write-Off Recommended"

        dialog.create_submission_btn.setVisible(show_buttons)
        dialog.approve_submission_btn.setVisible(show_buttons)

    @staticmethod
    def create_write_off_submission(dialog):
        """Open dialog to create a write-off submission"""
        from scripts.case_management_modules.write_off_submission_dialog import \
            WriteOffSubmissionDialog

        submission_dialog = WriteOffSubmissionDialog(dialog)
        submission_dialog.exec_()
        # Refresh the case list after creating submission
        ViewCasesLogic.refresh_cases(dialog)

    @staticmethod
    def approve_write_off_submission(dialog):
        """Open dialog to approve a write-off submission"""
        # Get available group IDs for approval
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT DISTINCT write_off_group_id
                FROM cases
                WHERE write_off_group_id IS NOT NULL AND lc_status = 'Write Off Recommended'
                ORDER BY write_off_group_id
            """
            )

            groups = cursor.fetchall()
            conn.close()

            if not groups:
                QMessageBox.information(
                    dialog,
                    "No Submissions",
                    "No write-off submissions available for approval.",
                )
                return

            # For now, just approve the first group (in a real app, you'd show a selection dialog)
            group_id = groups[0][0]

            from scripts.case_management_modules.write_off_management_dialog import \
                WriteOffApprovalDialog

            approval_dialog = WriteOffApprovalDialog(group_id, dialog)
            approval_dialog.exec_()
            # Refresh the case list after approval
            ViewCasesLogic.refresh_cases(dialog)

        except Exception as e:
            QMessageBox.critical(
                dialog, "Error", f"Failed to load submissions: {str(e)}"
            )
