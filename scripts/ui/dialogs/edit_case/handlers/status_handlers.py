"""
Status change handlers for the Edit Case dialog.

This module contains all event handlers related to status changes in the Edit Case dialog,
including status validation, UI updates, and workflow transitions.
"""

from typing import Any

from PyQt5.QtWidgets import QMessageBox

from scripts.Utilities.edit_case_status_display_utils import update_list_status_display


def select_responsibility(dialog: Any) -> None:
    """Handle responsibility selection for the case."""
    from scripts.case_management_modules.responsibility_selection import (
        ResponsibilitySelectionDialog,
    )

    selection_dialog = ResponsibilitySelectionDialog(dialog)
    if selection_dialog.exec_():
        selected = selection_dialog.get_selected_responsibility()
        if selected:
            dialog.responsibility_edit.setText(selected["name"])
            dialog.selected_responsibility_id = selected["id"]


def on_status_changed(dialog: Any, status: str) -> None:
    """
    Handle status selection change with special logic for Valid and Confirmed status.

    Args:
        dialog: The EditCaseDialog instance
        status: The selected status string
    """
    if status == "Valid":
        # Show warning dialog for Valid status
        reply = QMessageBox.question(
            dialog,
            "Confirm Valid Status",
            "Selecting 'Valid' means this case is NOT Fruitless and Wasteful Expenditure.\n\n"
            "Uploading Supporting Evidence is compulsory before the case can be saved.\n\n"
            "This will finalise the case.\n\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            dialog.supporting_evidence_compulsory = True
        else:
            # Revert to previous status or default
            dialog.status_combo.setCurrentText("Alleged")
            dialog.supporting_evidence_compulsory = False

        dialog.update_conditional_fields()

    elif status == "Confirmed":
        dialog.update_conditional_fields()
        dialog.lc_status_combo.setCurrentText("Awaiting LC determination")

    else:
        # Reset the compulsory flag for other statuses
        dialog.supporting_evidence_compulsory = False


def on_assessment_status_changed(dialog: Any, new_status: str) -> None:
    """
    Handle assessment status change with validation and UI updates.

    Args:
        dialog: The EditCaseDialog instance
        new_status: The new assessment status
    """
    print(f"Assessment status changed to: {new_status}")
    if new_status == "Valid":
        # Show warning dialog for Valid status
        reply = QMessageBox.question(
            dialog,
            "Confirm Valid Status",
            "Selecting 'Valid' means this case is NOT Fruitless and Wasteful Expenditure.\n\n"
            "Uploading Supporting Evidence is compulsory before the case can be saved.\n\n"
            "This will finalise the case.\n\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            dialog.supporting_evidence_compulsory = True
            update_conditional_fields(dialog)
        else:
            # Revert to previous status or default
            dialog.assessment_status_combo.setCurrentText("Alleged")
            dialog.supporting_evidence_compulsory = False
            return  # Don't update display

    elif new_status == "Confirmed":
        reply = QMessageBox.question(
            dialog,
            "Confirm Confirmed Status",
            "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
            "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        print(f"Reply for Confirmed: {reply}")
        if reply == QMessageBox.Yes:
            update_conditional_fields(dialog)
            # Update instance variables for instant grid update
            dialog.assessment_status = "Confirmed"
            dialog.lc_status = "Awaiting LC determination"
            # Only set LC status if it's not already set
            if dialog.lc_status_combo.currentText() == "":
                dialog.lc_status_combo.setCurrentText("Awaiting LC determination")
        else:
            dialog.assessment_status_combo.setCurrentText("Alleged")

    else:
        # Reset the compulsory flag for other statuses
        dialog.supporting_evidence_compulsory = False
        update_conditional_fields(dialog)

    # Update list status display
    update_list_status_display(dialog)


def on_lc_status_changed(dialog: Any, new_lc_status: str) -> None:
    """
    Handle loss control status change with workflow updates.

    Args:
        dialog: The EditCaseDialog instance
        new_lc_status: The new loss control status
    """
    print(f"LC status changed to: {new_lc_status}")

    # Update instance variable for instant grid update
    dialog.lc_status = new_lc_status

    # Handle workflow status changes - update suffixes and database
    from scripts.Utilities.workflow_utils import handle_loss_control_status_change

    success = handle_loss_control_status_change(
        dialog.case_id, dialog.base_transaction_no, new_lc_status
    )

    if not success:
        print(
            f"Warning: Failed to update workflow for LC status change to {new_lc_status}"
        )
        # Still update UI even if workflow update failed
        update_list_status_display(dialog)
        from .ui_updaters import update_lc_fields_visibility

        update_lc_fields_visibility(dialog, new_lc_status)
        return

    # Update grid instantly
    update_list_status_display(dialog)
    # Update field visibility dynamically
    from .ui_updaters import update_lc_fields_visibility

    update_lc_fields_visibility(dialog, new_lc_status)


def update_conditional_fields(dialog: Any) -> None:
    """
    Update visibility of conditional fields based on list and status selection.

    Args:
        dialog: The EditCaseDialog instance
    """
    try:
        # Safety checks for required widgets
        if not hasattr(dialog, "status_combo") or not hasattr(dialog, "category_combo"):
            return  # Exit early if required widgets don't exist

        # Get current selections safely
        # List information is now handled by the List Status Information group
        selected_list = dialog.selected_list or "Checklist"
        # Use assessment_status_combo if available (for edit case), otherwise status_combo
        if hasattr(dialog, "assessment_status_combo"):
            selected_status = (
                dialog.assessment_status_combo.currentText()
                if dialog.assessment_status_combo.count() > 0
                else ""
            )
        else:
            selected_status = (
                dialog.status_combo.currentText()
                if dialog.status_combo.count() > 0
                else ""
            )
        selected_category = (
            dialog.category_combo.currentText()
            if dialog.category_combo.count() > 0
            else ""
        )

        # Update status options based on list selection
        if hasattr(dialog, "status_combo"):
            current_status = dialog.status_combo.currentText()
            dialog.status_combo.clear()

            if selected_list == "Lead Schedule":
                dialog.status_combo.addItems(
                    [
                        "Alleged",
                        "Under Assessment",
                        "Valid",
                        "Confirmed",
                        "Recovered",
                        "Write Off Recommended",
                    ]
                )
            else:
                dialog.status_combo.addItems(
                    ["Alleged", "Under Assessment", "Valid", "Confirmed"]
                )

            # Restore previous selection if still valid
            if current_status and current_status in [
                dialog.status_combo.itemText(i)
                for i in range(dialog.status_combo.count())
            ]:
                dialog.status_combo.setCurrentText(current_status)
            else:
                dialog.status_combo.setCurrentText("Alleged")

        # Update category-based compulsory fields
        bas_comp = False
        persal_comp = False

        if selected_category and hasattr(dialog, "categories") and dialog.categories:
            category = next(
                (c for c in dialog.categories if c["name"] == selected_category), None
            )
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)

        # Update BAS fields visibility and labels (with safety checks)
        if hasattr(dialog, "bas_label"):
            dialog.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
            dialog.bas_label.setVisible(bas_comp)
        if hasattr(dialog, "bas_payment_no_edit"):
            dialog.bas_payment_no_edit.setVisible(bas_comp)
        if hasattr(dialog, "bas_date_label"):
            dialog.bas_date_label.setVisible(bas_comp)
        if hasattr(dialog, "bas_payment_date_edit"):
            dialog.bas_payment_date_edit.setVisible(bas_comp)

        # Update Persal field visibility and labels (with safety checks)
        if hasattr(dialog, "persal_label"):
            dialog.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
            dialog.persal_label.setVisible(persal_comp)
        if hasattr(dialog, "persal_no_edit"):
            dialog.persal_no_edit.setVisible(persal_comp)

        # Update assessment fields visibility (Valid/Confirmed)
        show_assessment = selected_status in ["Valid", "Confirmed"]

        # Update LC status combo visibility and options
        show_lc = (selected_status == "Confirmed") or dialog.lc_status
        if show_lc and hasattr(dialog, "lc_status_combo"):
            dialog.lc_status_combo.clear()
            dialog.lc_status_combo.addItems(
                ["Awaiting LC determination", "Recovered", "Write Off Recommended"]
            )
            dialog.lc_status_combo.setVisible(True)
            if hasattr(dialog, "lc_status_label"):
                dialog.lc_status_label.setVisible(True)
        elif hasattr(dialog, "lc_status_combo"):
            dialog.lc_status_combo.setVisible(False)
            if hasattr(dialog, "lc_status_label"):
                dialog.lc_status_label.setVisible(False)

        # Assessment fields (with safety checks)
        if hasattr(dialog, "source_doc_label"):
            dialog.source_doc_label.setVisible(show_assessment)
        if hasattr(dialog, "source_doc_edit"):
            dialog.source_doc_edit.setVisible(show_assessment)
        if hasattr(dialog, "source_doc_button"):
            dialog.source_doc_button.setVisible(show_assessment)

        if hasattr(dialog, "minutes_label"):
            dialog.minutes_label.setVisible(show_assessment)
        if hasattr(dialog, "minutes_edit"):
            dialog.minutes_edit.setVisible(show_assessment)
        if hasattr(dialog, "minutes_button"):
            dialog.minutes_button.setVisible(show_assessment)

        if hasattr(dialog, "assessment_evidence_label"):
            dialog.assessment_evidence_label.setVisible(show_assessment)
        if hasattr(dialog, "assessment_evidence_edit"):
            dialog.assessment_evidence_edit.setVisible(show_assessment)
        if hasattr(dialog, "evidence_button"):
            dialog.evidence_button.setVisible(show_assessment)

        # Set placeholders for required evidence fields
        if selected_status in ["Valid", "Confirmed"]:
            dialog.assessment_evidence_edit.setPlaceholderText(
                "Assessment Evidence is REQUIRED"
            )
            print("Setting assessment evidence placeholder to REQUIRED")
        if selected_status == "Confirmed":
            dialog.supporting_evidence_edit.setPlaceholderText(
                "Supporting Evidence is REQUIRED"
            )
            print("Setting supporting evidence placeholder to REQUIRED")

        # Set required labels visibility based on status
        if hasattr(dialog, "assessment_evidence_label"):
            new_text = "Assessment Evidence" + (
                " (REQUIRED)" if selected_status in ["Valid", "Confirmed"] else ""
            )
            dialog.assessment_evidence_label.setText(new_text)
            print(f"DEBUG: Updated assessment_evidence_label text to: {new_text}")
        if hasattr(dialog, "supporting_evidence_label"):
            new_text = "Supporting Evidence Document" + (
                " (REQUIRED)" if selected_status == "Confirmed" else ""
            )
            dialog.supporting_evidence_label.setText(new_text)
            print(f"DEBUG: Updated supporting_evidence_label text to: {new_text}")

        # Show/hide Persal No field based on category
        if hasattr(dialog, "persal_label") and hasattr(dialog, "persal_no_edit"):
            selected_category = (
                dialog.category_combo.currentText()
                if dialog.category_combo.count() > 0
                else ""
            )
            is_hr_related = "HR Related" in selected_category
            dialog.persal_label.setVisible(is_hr_related)
            dialog.persal_no_edit.setVisible(is_hr_related)
            print(
                f"DEBUG: Persal No field visibility: {is_hr_related} for category: {selected_category}"
            )

    except Exception as e:
        print(f"Warning: Error in update_conditional_fields: {e}")
        # Don't crash, just continue with default visibility
