from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from scripts.case_management_modules.responsibility_selection import \
    ResponsibilitySelectionDialog
from scripts.Utilities.edit_case_status_display_utils import \
    update_list_status_display


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


def update_conditional_fields(dialog):
    """Update visibility of conditional fields based on list and status selection"""
    try:
        # Safety checks for required widgets
        if (
            not hasattr(dialog, "status_combo")
            or not hasattr(dialog, "category_combo")
        ):
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
        # if hasattr(dialog, 'assessment_required_label'):
        #     dialog.assessment_required_label.setVisible(show_assessment)

        if hasattr(dialog, "assessed_by_label"):
            dialog.assessed_by_label.setVisible(show_assessment)
        if hasattr(dialog, "assessed_by_edit"):
            dialog.assessed_by_edit.setVisible(show_assessment)

        if hasattr(dialog, "assessment_date_label"):
            dialog.assessment_date_label.setVisible(show_assessment)
        if hasattr(dialog, "assessment_date_edit"):
            dialog.assessment_date_edit.setVisible(show_assessment)

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
        # assessment_visible = selected_status in ["Valid", "Confirmed"]
        # dialog.assessment_required_label.setVisible(assessment_visible)
        # print(f"Setting assessment required label visible: {assessment_visible} for status {selected_status}")

        # supporting_visible = selected_status == "Confirmed"
        # dialog.supporting_required_label.setVisible(supporting_visible)
        # print(f"Setting supporting required label visible: {supporting_visible} for status {selected_status}")

        # Update label texts for required fields
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
            selected_category = dialog.category_combo.currentText() if dialog.category_combo.count() > 0 else ""
            is_hr_related = "HR Related" in selected_category
            dialog.persal_label.setVisible(is_hr_related)
            dialog.persal_no_edit.setVisible(is_hr_related)
            print(f"DEBUG: Persal No field visibility: {is_hr_related} for category: {selected_category}")

    except Exception as e:
        print(f"Warning: Error in update_conditional_fields: {e}")
        # Don't crash, just continue with default visibility


def browse_source_doc(dialog):
    """Handle browsing for source document"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Source Document", "", "PDF Files (*.pdf)"
    )
    if file_path:
        dialog.source_doc_edit.setText(file_path)


def browse_minutes(dialog):
    """Handle browsing for minutes"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Minutes", "", "PDF Files (*.pdf)"
    )
    if file_path:
        dialog.minutes_edit.setText(file_path)


def browse_evidence(dialog):
    """Handle browsing for evidence"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Evidence", "", "PDF Files (*.pdf)"
    )
    if file_path:
        print(f"Setting evidence_edit to: {file_path}")
        dialog.evidence_edit.setText(file_path)
        print(f"evidence_edit text: {dialog.evidence_edit.text()}")


def browse_assessment_evidence(dialog):
    """Handle browsing for assessment evidence"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Assessment Evidence", "", "PDF Files (*.pdf)"
    )
    if file_path:
        print(f"Setting assessment_evidence_edit to: {file_path}")
        dialog.assessment_evidence_edit.setText(file_path)
        print(
            f"assessment_evidence_edit text: {dialog.assessment_evidence_edit.text()}"
        )


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
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Recovery Evidence", "", "PDF Files (*.pdf)"
    )
    if file_path:
        dialog.recovery_evidence_edit.setText(file_path)


def browse_supporting_evidence(dialog):
    """Handle browsing for supporting evidence"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Supporting Evidence", "", "PDF Files (*.pdf)"
    )
    if file_path:
        dialog.supporting_evidence_edit.setText(file_path)


def view_assessment_evidence(dialog):
    """View assessment evidence file"""
    if (
        hasattr(dialog, "assessment_evidence_edit")
        and dialog.assessment_evidence_edit.text()
    ):
        import os

        os.startfile(dialog.assessment_evidence_edit.text())


def view_recovery_evidence(dialog):
    """View recovery evidence file"""
    if (
        hasattr(dialog, "recovery_evidence_edit")
        and dialog.recovery_evidence_edit.text()
    ):
        import os

        os.startfile(dialog.recovery_evidence_edit.text())


def browse_recovery_evidence_rip(dialog):
    """Handle browsing for recovery evidence in Recovery in Progress group"""
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select Recovery Evidence", "", "PDF Files (*.pdf)"
    )
    if file_path:
        dialog.recovery_evidence_rip_edit.setText(file_path)


def view_recovery_evidence_rip(dialog):
    """View recovery evidence file in Recovery in Progress group"""
    if (
        hasattr(dialog, "recovery_evidence_rip_edit")
        and dialog.recovery_evidence_rip_edit.text()
    ):
        import os

        os.startfile(dialog.recovery_evidence_rip_edit.text())


def view_minutes(dialog):
    """View minutes file"""
    if hasattr(dialog, "minutes_edit") and dialog.minutes_edit.text():
        import os

        os.startfile(dialog.minutes_edit.text())


def view_supporting_evidence(dialog):
    """View supporting evidence file"""
    if (
        hasattr(dialog, "supporting_evidence_edit")
        and dialog.supporting_evidence_edit.text()
    ):
        import os

        os.startfile(dialog.supporting_evidence_edit.text())


def view_source_doc(dialog):
    """View source document file"""
    if hasattr(dialog, "source_doc_edit") and dialog.source_doc_edit.text():
        import os

        os.startfile(dialog.source_doc_edit.text())


def update_list_status_grid(dialog, list_name, status):
    """Update list status grid"""
    if list_name == "Checklist" and status == "Confirmed":
        # Set LC status in table to "Awaiting LC determination"
        dialog.list_status_table.setItem(
            1, 1, QTableWidgetItem("Awaiting LC determination")
        )  # Assuming row 1 is LC status
    print(f"Updating grid for {list_name} with status {status}")


def select_bas_payment_date(dialog):
    """Select BAS payment date"""
    from PyQt5.QtWidgets import (QCalendarWidget, QDialog, QPushButton,
                                 QVBoxLayout)

    # Implementation for date selection dialog
    print("BAS payment date selection")


def select_bas_journal_date(dialog):
    """Select BAS journal date"""
    from PyQt5.QtWidgets import (QCalendarWidget, QDialog, QPushButton,
                                 QVBoxLayout)

    # Implementation for date selection dialog
    print("BAS journal date selection")


def select_latest_installment_date(dialog):
    """Select latest installment date using date picker"""
    from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout
    from PyQt5.QtCore import QDate

    calendar_dialog = QDialog(dialog)
    calendar_dialog.setWindowTitle("Select Latest Installment Date")
    calendar_dialog.setFixedSize(300, 250)

    layout = QVBoxLayout(calendar_dialog)
    calendar = QCalendarWidget()
    layout.addWidget(calendar)

    def on_date_selected():
        selected_date = calendar.selectedDate()
        dialog.latest_installment_date_edit.setText(selected_date.toString("yyyy-MM-dd"))
        calendar_dialog.accept()

    calendar.clicked.connect(on_date_selected)
    calendar_dialog.exec_()
    print("Latest installment date selection")


def update_lc_fields_visibility(dialog, lc_status):
    """
    Update visibility of LC-specific fields based on LC status.

    Args:
        dialog: The EditCaseDialog instance.
        lc_status (str): The current LC status.
    """
    print(f"LC fields updated for status: {lc_status}")
    
    # Update recovery group visibility based on LC status
    if hasattr(dialog, "recovery_group"):
        if lc_status == "Recovery in Progress":
            dialog.recovery_group.setVisible(True)
            # Initialize recovery progress when group becomes visible
            update_recovery_progress(dialog)
        else:
            dialog.recovery_group.setVisible(False)
    
    # Update recovery fields visibility based on LC status
    if lc_status == "Recovery in Progress":
        # Show recovery fields for installment tracking
        if hasattr(dialog, 'debtor_name_edit'):
            dialog.debtor_name_edit.setVisible(True)
        if hasattr(dialog, 'debtor_number_edit'):
            dialog.debtor_number_edit.setVisible(True)
        if hasattr(dialog, 'debt_number_edit'):
            dialog.debt_number_edit.setVisible(True)
        
        # Hide Loss Control Committee recovery evidence, show Recovery in Progress recovery evidence
        if hasattr(dialog, 'recovery_evidence_label'):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_button'):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_view_button'):
            dialog.recovery_evidence_view_button.setVisible(False)
        
        # Show Recovery in Progress recovery evidence
        if hasattr(dialog, 'recovery_evidence_rip_label'):
            dialog.recovery_evidence_rip_label.setVisible(True)
        if hasattr(dialog, 'recovery_evidence_rip_edit'):
            dialog.recovery_evidence_rip_edit.setVisible(True)
            dialog.recovery_evidence_rip_edit.setPlaceholderText("Upload latest Debt Inquiry report")
        if hasattr(dialog, 'recovery_evidence_rip_button'):
            dialog.recovery_evidence_rip_button.setVisible(True)
        if hasattr(dialog, 'recovery_evidence_rip_view_button'):
            dialog.recovery_evidence_rip_view_button.setVisible(True)
        
        if hasattr(dialog, 'minutes_edit'):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
        
    elif lc_status == "Recovered":
        # Hide installment fields, show only total recovered
        if hasattr(dialog, 'debtor_name_edit'):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, 'debtor_number_edit'):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, 'debt_number_edit'):
            dialog.debt_number_edit.setVisible(False)
        
        # Show Loss Control Committee recovery evidence, hide Recovery in Progress recovery evidence
        if hasattr(dialog, 'recovery_evidence_label'):
            dialog.recovery_evidence_label.setVisible(True)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.setVisible(True)
            dialog.recovery_evidence_edit.setPlaceholderText("Recovery Evidence is REQUIRED")
        if hasattr(dialog, 'recovery_evidence_button'):
            dialog.recovery_evidence_button.setVisible(True)
        if hasattr(dialog, 'recovery_evidence_view_button'):
            dialog.recovery_evidence_view_button.setVisible(True)
        
        # Hide Recovery in Progress recovery evidence
        if hasattr(dialog, 'recovery_evidence_rip_label'):
            dialog.recovery_evidence_rip_label.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_rip_edit'):
            dialog.recovery_evidence_rip_edit.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_rip_button'):
            dialog.recovery_evidence_rip_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_rip_view_button'):
            dialog.recovery_evidence_rip_view_button.setVisible(False)
        if hasattr(dialog, 'minutes_edit'):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
        
    elif lc_status == "Write Off Recommended":
        # Hide all recovery fields
        if hasattr(dialog, 'debtor_name_edit'):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, 'debtor_number_edit'):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, 'debt_number_edit'):
            dialog.debt_number_edit.setVisible(False)
        
        if hasattr(dialog, 'recovery_evidence_label'):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_button'):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_view_button'):
            dialog.recovery_evidence_view_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.clear()
            dialog.recovery_evidence_edit.setPlaceholderText("")
        if hasattr(dialog, 'minutes_edit'):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
        
    else:
        # Hide all recovery fields for other statuses
        if hasattr(dialog, 'debtor_name_edit'):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, 'debtor_number_edit'):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, 'debt_number_edit'):
            dialog.debt_number_edit.setVisible(False)
        
        if hasattr(dialog, 'recovery_evidence_label'):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_button'):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_view_button'):
            dialog.recovery_evidence_view_button.setVisible(False)
        if hasattr(dialog, 'recovery_evidence_edit'):
            dialog.recovery_evidence_edit.clear()
            dialog.recovery_evidence_edit.setPlaceholderText("")
        if hasattr(dialog, 'minutes_edit'):
            dialog.minutes_edit.setPlaceholderText("")


def select_new_installment_date(dialog):
    """Handle new installment date selection with calendar popup"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget
    from PyQt5.QtCore import QDate

    calendar_dialog = QDialog(dialog)
    calendar_dialog.setWindowTitle("Select Installment Date")
    calendar_dialog.setFixedSize(520, 380)

    layout = QVBoxLayout(calendar_dialog)
    calendar = QCalendarWidget()
    layout.addWidget(calendar)

    def on_date_selected():
        selected_date = calendar.selectedDate()
        dialog.new_installment_date_edit.setText(selected_date.toString("yyyy-MM-dd"))
        calendar_dialog.accept()

    calendar.clicked.connect(on_date_selected)
    calendar_dialog.exec_()


def add_new_installment(dialog):
    """Add a new installment to the recovery tracking"""
    try:
        # Validate installment amount
        amount_text = dialog.new_installment_amount_edit.text().strip()
        if not amount_text:
            QMessageBox.warning(dialog, "Validation Error", "Please enter an installment amount.")
            return
        
        try:
            installment_amount = float(amount_text)
            if installment_amount <= 0:
                QMessageBox.warning(dialog, "Validation Error", "Installment amount must be greater than zero.")
                return
        except ValueError:
            QMessageBox.warning(dialog, "Validation Error", "Please enter a valid amount.")
            return

        # Validate installment date
        date_text = dialog.new_installment_date_edit.text().strip()
        if not date_text:
            QMessageBox.warning(dialog, "Validation Error", "Please select an installment date.")
            return

        recovery_evidence_path = ""
        if hasattr(dialog, "recovery_evidence_rip_edit"):
            recovery_evidence_path = dialog.recovery_evidence_rip_edit.text().strip()
        elif hasattr(dialog, "recovery_evidence_edit"):
            recovery_evidence_path = dialog.recovery_evidence_edit.text().strip()

        if not recovery_evidence_path:
            QMessageBox.warning(
                dialog,
                "Recovery Evidence Required",
                "Recovery evidence must be uploaded before recording installments.",
            )
            return

        import os

        if not os.path.exists(recovery_evidence_path):
            QMessageBox.warning(
                dialog,
                "Recovery Evidence Missing",
                (
                    "The selected recovery evidence file could not be accessed.\n\n"
                    "Please ensure the file still exists or re-upload it before recording installments."
                ),
            )
            return

        # Get current recovery data
        current_amount_paid = get_current_amount_paid(dialog)
        original_amount = get_original_amount(dialog)
        
        # Check if installment would exceed original amount
        new_total = current_amount_paid + installment_amount
        if new_total > original_amount:
            QMessageBox.warning(
                dialog, 
                "Validation Error", 
                f"Installment would exceed original amount.\n"
                f"Original: R {original_amount:.2f}\n"
                f"Already paid: R {current_amount_paid:.2f}\n"
                f"Remaining: R {original_amount - current_amount_paid:.2f}"
            )
            return

        # Save installment to database
        if save_installment_to_database(dialog, installment_amount, date_text):
            # Update recovery progress
            update_recovery_progress(dialog)
            
            # Clear form
            dialog.new_installment_amount_edit.clear()
            dialog.new_installment_date_edit.clear()
            
            # Check if fully recovered
            if new_total >= original_amount:
                finalize_recovery(dialog)
            
            QMessageBox.information(dialog, "Success", f"Installment of R {installment_amount:.2f} added successfully!")
        else:
            QMessageBox.critical(dialog, "Error", "Failed to save installment. Please try again.")
            
    except Exception as e:
        QMessageBox.critical(dialog, "Error", f"An error occurred: {str(e)}")


def view_installment_history(dialog):
    """Open installment history dialog"""
    try:
        # For now, show a simple message box with installment summary
        current_amount_paid = get_current_amount_paid(dialog)
        original_amount = get_original_amount(dialog)
        remaining_amount = original_amount - current_amount_paid
        
        QMessageBox.information(
            dialog,
            "Installment History",
            f"Recovery Progress Summary:\n\n"
            f"Original Amount: R {original_amount:.2f}\n"
            f"Amount Paid: R {current_amount_paid:.2f}\n"
            f"Remaining: R {remaining_amount:.2f}\n\n"
            f"Progress: {(current_amount_paid/original_amount*100):.1f}%"
        )
    except Exception as e:
        QMessageBox.critical(dialog, "Error", f"Failed to open installment history: {str(e)}")


def update_recovery_progress(dialog):
    """Update recovery progress display"""
    try:
        original_amount = get_original_amount(dialog)
        amount_paid = get_current_amount_paid(dialog)
        remaining_amount = original_amount - amount_paid
        
        # Update labels
        dialog.original_amount_label.setText(f"R {original_amount:.2f}")
        dialog.amount_paid_label.setText(f"R {amount_paid:.2f}")
        dialog.remaining_amount_label.setText(f"R {remaining_amount:.2f}")
        
        # Update recovery status
        if amount_paid == 0:
            dialog.loss_recovery_status_label.setText("N/A")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #666; padding: 5px; border: 1px solid #ddd; background-color: #f9f9f9; }"
            )
        elif remaining_amount > 0:
            dialog.loss_recovery_status_label.setText("In Progress")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #ff9800; padding: 5px; border: 1px solid #ddd; background-color: #fff3e0; }"
            )
        else:
            dialog.loss_recovery_status_label.setText("Completed")
            dialog.loss_recovery_status_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #4caf50; padding: 5px; border: 1px solid #ddd; background-color: #f1f8e9; }"
            )
            
    except Exception as e:
        print(f"Error updating recovery progress: {e}")


def get_original_amount(dialog):
    """Get the original case amount"""
    try:
        amount_text = dialog.amount_edit.text().strip()
        if amount_text:
            return float(amount_text)
        return 0.0
    except (ValueError, AttributeError):
        return 0.0


def get_current_amount_paid(dialog):
    """Get current total amount paid from database"""
    try:
        import sqlite3
        from scripts.Utilities.config import DB_PATH
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get total from installments table
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM installments WHERE case_id = ?",
            (dialog.case_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return float(result[0]) if result else 0.0
    except Exception as e:
        print(f"Error getting current amount paid: {e}")
        return 0.0


def save_installment_to_database(dialog, amount, date):
    """Save installment to database"""
    try:
        import json
        import os
        import sqlite3
        from datetime import datetime
        from scripts.Utilities.config import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Prefer evidence selected in the current dialog session
        ui_recovery_path = ""
        if hasattr(dialog, "recovery_evidence_rip_edit"):
            ui_recovery_path = dialog.recovery_evidence_rip_edit.text().strip()
        if not ui_recovery_path and hasattr(dialog, "recovery_evidence_edit"):
            ui_recovery_path = dialog.recovery_evidence_edit.text().strip()

        if ui_recovery_path:
            if not os.path.exists(ui_recovery_path):
                conn.close()
                QMessageBox.warning(
                    dialog,
                    "Recovery Evidence Missing",
                    (
                        "The selected recovery evidence file could not be accessed.\n\n"
                        "Please ensure the file still exists or re-upload it before recording installments."
                    ),
                )
                return False
            recovery_path = ui_recovery_path
        else:
            # Fall back to evidence already stored on the case record
            cursor.execute(
                "SELECT recovery_evidence_path, evidence_paths FROM cases WHERE id = ?",
                (dialog.case_id,),
            )
            case_row = cursor.fetchone()

            recovery_path = ""
            if case_row:
                recovery_path = case_row[0] or ""
                evidence_json = case_row[1]
                if not recovery_path and evidence_json:
                    try:
                        evidence_dict = json.loads(evidence_json)
                        recovery_path = evidence_dict.get("recovery") or ""
                    except json.JSONDecodeError:
                        recovery_path = ""

            if not recovery_path:
                conn.close()
                QMessageBox.warning(
                    dialog,
                    "Recovery Evidence Required",
                    "Recovery evidence must be uploaded before recording installments.",
                )
                return False

            if not os.path.exists(recovery_path):
                conn.close()
                QMessageBox.warning(
                    dialog,
                    "Recovery Evidence Missing",
                    (
                        "Stored recovery evidence could not be located.\n\n"
                        "Please re-upload the evidence before recording installments."
                    ),
                )
                return False

        # Create installments table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installments (
                id INTEGER PRIMARY KEY,
                case_id INTEGER,
                amount REAL,
                installment_date TEXT,
                created_at TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)
        
        # Insert installment
        cursor.execute("""
            INSERT INTO installments (case_id, amount, installment_date, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            dialog.case_id,
            amount,
            date,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving installment: {e}")
        return False


def finalize_recovery(dialog):
    """Finalize recovery when fully paid"""
    try:
        # Update case status to Recovered
        dialog.lc_status_combo.setCurrentText("Recovered")
        
        # Update list status
        dialog.update_list_status_grid("Recovered", "Recovered")
        dialog.update_list_status_grid("Recovery in Progress", "N/A")
        
        # Update workflow - this will add -REC suffix and remove -RIP suffix
        from scripts.Utilities.workflow_utils import handle_loss_control_status_change
        success = handle_loss_control_status_change(
            dialog.case_id,
            dialog.base_transaction_no,
            "Recovered"
        )
        
        if success:
            # Update the dialog's suffixes to reflect the change
            # dialog.suffixes is already a list, so we work with it directly
            if isinstance(dialog.suffixes, list):
                dialog.suffixes = [s for s in dialog.suffixes if s != "-RIP"]
                if "-REC" not in dialog.suffixes:
                    dialog.suffixes.append("-REC")
            else:
                # If it's a string, convert to list first
                suffix_list = dialog.suffixes.split(",") if dialog.suffixes else []
                suffix_list = [s for s in suffix_list if s != "-RIP"]
                if "-REC" not in suffix_list:
                    suffix_list.append("-REC")
                dialog.suffixes = suffix_list
            
            # Update the transaction number display
            from scripts.Utilities.workflow_utils import get_display_transaction_no
            display_transaction_no = get_display_transaction_no(
                dialog.base_transaction_no, dialog.suffixes
            )
            dialog.trans_no_edit.setText(display_transaction_no)
            
            QMessageBox.information(
                dialog, 
                "Recovery Completed", 
                "This case has been fully recovered and moved to the Recovered list!"
            )
        else:
            QMessageBox.warning(
                dialog, 
                "Warning", 
                "Recovery completed but workflow update failed. Please refresh the case."
            )
        
    except Exception as e:
        print(f"Error finalizing recovery: {e}")
        QMessageBox.warning(dialog, "Warning", f"Recovery completed but status update failed: {str(e)}")
