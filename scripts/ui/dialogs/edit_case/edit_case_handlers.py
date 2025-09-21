from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from scripts.case_management_modules.responsibility_selection import ResponsibilitySelectionDialog
from scripts.Utilities.edit_case_status_display_utils import update_list_status_display


def select_responsibility(dialog):
    """Handle responsibility selection"""
    selection_dialog = ResponsibilitySelectionDialog(dialog)
    if selection_dialog.exec_():
        selected = selection_dialog.get_selected_responsibility()
        if selected:
            dialog.responsibility_edit.setText(selected["name"])
            dialog.selected_responsibility_id = selected["id"]


def on_status_changed(dialog, status):
    """Handle status selection change with special logic for Valid and Confirmed status"""
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
            QMessageBox.No
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


def update_conditional_fields(dialog):
    """Update visibility of conditional fields based on list and status selection"""
    try:
        # Safety checks for required widgets
        if not hasattr(dialog, 'list_combo') or not hasattr(dialog, 'status_combo') or not hasattr(dialog, 'category_combo'):
            return  # Exit early if required widgets don't exist

        # Get current selections safely
        selected_list = dialog.list_combo.currentText() if dialog.list_combo.count() > 0 else ""
        # Use assessment_status_combo if available (for edit case), otherwise status_combo
        if hasattr(dialog, 'assessment_status_combo'):
            selected_status = dialog.assessment_status_combo.currentText() if dialog.assessment_status_combo.count() > 0 else ""
        else:
            selected_status = dialog.status_combo.currentText() if dialog.status_combo.count() > 0 else ""
        selected_category = dialog.category_combo.currentText() if dialog.category_combo.count() > 0 else ""

        # Update status options based on list selection
        if hasattr(dialog, 'status_combo'):
            current_status = dialog.status_combo.currentText()
            dialog.status_combo.clear()

            if selected_list == "Lead Schedule":
                dialog.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed", "Recovered", "Write Off Recommended"])
            else:
                dialog.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])

            # Restore previous selection if still valid
            if current_status and current_status in [dialog.status_combo.itemText(i) for i in range(dialog.status_combo.count())]:
                dialog.status_combo.setCurrentText(current_status)
            else:
                dialog.status_combo.setCurrentText("Alleged")

        # Update category-based compulsory fields
        bas_comp = False
        persal_comp = False

        if selected_category and hasattr(dialog, 'categories') and dialog.categories:
            category = next((c for c in dialog.categories if c["name"] == selected_category), None)
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)

        # Update BAS fields visibility and labels (with safety checks)
        if hasattr(dialog, 'bas_label'):
            dialog.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
            dialog.bas_label.setVisible(bas_comp)
        if hasattr(dialog, 'bas_payment_no_edit'):
            dialog.bas_payment_no_edit.setVisible(bas_comp)
        if hasattr(dialog, 'bas_date_label'):
            dialog.bas_date_label.setVisible(bas_comp)
        if hasattr(dialog, 'bas_payment_date_edit'):
            dialog.bas_payment_date_edit.setVisible(bas_comp)

        # Update Persal field visibility and labels (with safety checks)
        if hasattr(dialog, 'persal_label'):
            dialog.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
            dialog.persal_label.setVisible(persal_comp)
        if hasattr(dialog, 'persal_no_edit'):
            dialog.persal_no_edit.setVisible(persal_comp)

        # Update assessment fields visibility (Valid/Confirmed)
        show_assessment = selected_status in ["Valid", "Confirmed"]

        # Update LC status combo visibility and options
        show_lc = (selected_status == "Confirmed") or dialog.lc_status
        if show_lc and hasattr(dialog, 'lc_status_combo'):
            dialog.lc_status_combo.clear()
            dialog.lc_status_combo.addItems(["Awaiting LC determination", "Recovered", "Write Off Recommended"])
            dialog.lc_status_combo.setVisible(True)
            if hasattr(dialog, 'lc_status_label'):
                dialog.lc_status_label.setVisible(True)
        elif hasattr(dialog, 'lc_status_combo'):
            dialog.lc_status_combo.setVisible(False)
            if hasattr(dialog, 'lc_status_label'):
                dialog.lc_status_label.setVisible(False)

        # Assessment fields (with safety checks)
        if hasattr(dialog, 'source_doc_label'):
            dialog.source_doc_label.setVisible(show_assessment)
        if hasattr(dialog, 'source_doc_edit'):
            dialog.source_doc_edit.setVisible(show_assessment)
        if hasattr(dialog, 'source_doc_button'):
            dialog.source_doc_button.setVisible(show_assessment)

        if hasattr(dialog, 'minutes_label'):
            dialog.minutes_label.setVisible(show_assessment)
        if hasattr(dialog, 'minutes_edit'):
            dialog.minutes_edit.setVisible(show_assessment)
        if hasattr(dialog, 'minutes_button'):
            dialog.minutes_button.setVisible(show_assessment)

        if hasattr(dialog, 'assessment_evidence_label'):
            dialog.assessment_evidence_label.setVisible(show_assessment)
        if hasattr(dialog, 'assessment_evidence_edit'):
            dialog.assessment_evidence_edit.setVisible(show_assessment)
        if hasattr(dialog, 'evidence_button'):
            dialog.evidence_button.setVisible(show_assessment)
        # if hasattr(dialog, 'assessment_required_label'):
        #     dialog.assessment_required_label.setVisible(show_assessment)

        if hasattr(dialog, 'assessed_by_label'):
            dialog.assessed_by_label.setVisible(show_assessment)
        if hasattr(dialog, 'assessed_by_edit'):
            dialog.assessed_by_edit.setVisible(show_assessment)

        if hasattr(dialog, 'assessment_date_label'):
            dialog.assessment_date_label.setVisible(show_assessment)
        if hasattr(dialog, 'assessment_date_edit'):
            dialog.assessment_date_edit.setVisible(show_assessment)

        # Set placeholders for required evidence fields
        if selected_status in ["Valid", "Confirmed"]:
            dialog.assessment_evidence_edit.setPlaceholderText("Assessment Evidence is REQUIRED")
            print("Setting assessment evidence placeholder to REQUIRED")
        if selected_status == "Confirmed":
            dialog.supporting_evidence_edit.setPlaceholderText("Supporting Evidence is REQUIRED")
            print("Setting supporting evidence placeholder to REQUIRED")

        # Set required labels visibility based on status
        # assessment_visible = selected_status in ["Valid", "Confirmed"]
        # dialog.assessment_required_label.setVisible(assessment_visible)
        # print(f"Setting assessment required label visible: {assessment_visible} for status {selected_status}")

        # supporting_visible = selected_status == "Confirmed"
        # dialog.supporting_required_label.setVisible(supporting_visible)
        # print(f"Setting supporting required label visible: {supporting_visible} for status {selected_status}")

        # Update label texts for required fields
        if hasattr(dialog, 'assessment_evidence_label'):
            new_text = "Assessment Evidence" + (" (REQUIRED)" if selected_status in ["Valid", "Confirmed"] else "")
            dialog.assessment_evidence_label.setText(new_text)
            print(f"DEBUG: Updated assessment_evidence_label text to: {new_text}")
        if hasattr(dialog, 'supporting_evidence_label'):
            new_text = "Supporting Evidence Document" + (" (REQUIRED)" if selected_status == "Confirmed" else "")
            dialog.supporting_evidence_label.setText(new_text)
            print(f"DEBUG: Updated supporting_evidence_label text to: {new_text}")

    except Exception as e:
        print(f"Warning: Error in update_conditional_fields: {e}")
        # Don't crash, just continue with default visibility


def browse_source_doc(dialog):
    """Handle browsing for source document"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Source Document", "", "PDF Files (*.pdf)")
    if file_path:
        dialog.source_doc_edit.setText(file_path)


def browse_minutes(dialog):
    """Handle browsing for minutes"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Minutes", "", "PDF Files (*.pdf)")
    if file_path:
        dialog.minutes_edit.setText(file_path)


def browse_evidence(dialog):
    """Handle browsing for evidence"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Evidence", "", "PDF Files (*.pdf)")
    if file_path:
        print(f"Setting evidence_edit to: {file_path}")
        dialog.evidence_edit.setText(file_path)
        print(f"evidence_edit text: {dialog.evidence_edit.text()}")


def browse_assessment_evidence(dialog):
    """Handle browsing for assessment evidence"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Assessment Evidence", "", "PDF Files (*.pdf)")
    if file_path:
        print(f"Setting assessment_evidence_edit to: {file_path}")
        dialog.assessment_evidence_edit.setText(file_path)
        print(f"assessment_evidence_edit text: {dialog.assessment_evidence_edit.text()}")


def on_save_clicked(dialog):
    """Handle save button click"""
    dialog.logic.save_case()


def on_cancel_clicked(dialog):
    """Handle cancel button click"""
    dialog.reject()
def on_assessment_status_changed(dialog, new_status):
    # Handle assessment status change
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
            QMessageBox.No
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
        reply = QMessageBox.question(dialog, "Confirm Confirmed Status",
            "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
            "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
            "Do you want to proceed?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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


def on_lc_status_changed(dialog, new_lc_status):
    # Handle loss control status change
    print(f"LC status changed to: {new_lc_status}")
    # Update instance variable for instant grid update
    dialog.lc_status = new_lc_status
    # Update grid instantly
    update_list_status_display(dialog)
    # Update field visibility dynamically
    update_lc_fields_visibility(dialog, new_lc_status)


def browse_recovery_evidence(dialog):
    """Handle browsing for recovery evidence"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Recovery Evidence", "", "PDF Files (*.pdf)")
    if file_path:
        dialog.recovery_evidence_edit.setText(file_path)


def browse_supporting_evidence(dialog):
    """Handle browsing for supporting evidence"""
    file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Supporting Evidence", "", "PDF Files (*.pdf)")
    if file_path:
        dialog.supporting_evidence_edit.setText(file_path)


def view_assessment_evidence(dialog):
    """View assessment evidence file"""
    if hasattr(dialog, 'assessment_evidence_edit') and dialog.assessment_evidence_edit.text():
        import os
        os.startfile(dialog.assessment_evidence_edit.text())


def view_recovery_evidence(dialog):
    """View recovery evidence file"""
    if hasattr(dialog, 'recovery_evidence_edit') and dialog.recovery_evidence_edit.text():
        import os
        os.startfile(dialog.recovery_evidence_edit.text())


def view_minutes(dialog):
    """View minutes file"""
    if hasattr(dialog, 'minutes_edit') and dialog.minutes_edit.text():
        import os
        os.startfile(dialog.minutes_edit.text())


def view_supporting_evidence(dialog):
    """View supporting evidence file"""
    if hasattr(dialog, 'supporting_evidence_edit') and dialog.supporting_evidence_edit.text():
        import os
        os.startfile(dialog.supporting_evidence_edit.text())


def view_source_doc(dialog):
    """View source document file"""
    if hasattr(dialog, 'source_doc_edit') and dialog.source_doc_edit.text():
        import os
        os.startfile(dialog.source_doc_edit.text())


def update_list_status_grid(dialog, list_name, status):
    """Update list status grid"""
    if list_name == "Checklist" and status == "Confirmed":
        # Set LC status in table to "Awaiting LC determination"
        dialog.list_status_table.setItem(1, 1, QTableWidgetItem("Awaiting LC determination"))  # Assuming row 1 is LC status
    print(f"Updating grid for {list_name} with status {status}")


def select_bas_payment_date(dialog):
    """Select BAS payment date"""
    from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout, QPushButton
    # Implementation for date selection dialog
    print("BAS payment date selection")


def select_bas_journal_date(dialog):
    """Select BAS journal date"""
    from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout, QPushButton
    # Implementation for date selection dialog
    print("BAS journal date selection")
def update_lc_fields_visibility(dialog, lc_status):
    """
    Update visibility of LC-specific fields based on LC status.
    
    Args:
        dialog: The EditCaseDialog instance.
        lc_status (str): The current LC status.
    """
    print(f"LC fields updated for status: {lc_status}")
    if lc_status == "Recovered":
        dialog.recovery_evidence_label.setVisible(True)
        dialog.recovery_evidence_edit.setVisible(True)
        dialog.recovery_evidence_button.setVisible(True)
        dialog.recovery_evidence_view_button.setVisible(True)
        dialog.recovery_evidence_edit.setPlaceholderText("Recovery Evidence is REQUIRED")
        dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
    elif lc_status == "Write Off Recommended":
        dialog.recovery_evidence_label.setVisible(False)
        dialog.recovery_evidence_edit.setVisible(False)
        dialog.recovery_evidence_button.setVisible(False)
        dialog.recovery_evidence_view_button.setVisible(False)
        dialog.recovery_evidence_edit.clear()
        dialog.recovery_evidence_edit.setPlaceholderText("")
        dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
    else:
        dialog.recovery_evidence_label.setVisible(False)
        dialog.recovery_evidence_edit.setVisible(False)
        dialog.recovery_evidence_button.setVisible(False)
        dialog.recovery_evidence_view_button.setVisible(False)
        dialog.recovery_evidence_edit.clear()
        dialog.recovery_evidence_edit.setPlaceholderText("")
        dialog.minutes_edit.setPlaceholderText("")