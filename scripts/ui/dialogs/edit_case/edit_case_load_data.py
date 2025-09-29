"""
Load case data utilities for EditCaseDialog.
Handles loading existing case data into the form fields.
"""

import json

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (QDateEdit, QFormLayout, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit,
                             QWidget)
from scripts.Utilities.edit_case_status_display_utils import \
    update_list_status_display


def load_case_data_components(dialog_instance):
    """
    Load existing case data into the form fields.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # Explicitly clear the assessment evidence field to prevent status text from appearing
    # dialog_instance.evidence_edit.setText('')

    # Temporarily disconnect signals to prevent triggering during loading
    try:
        dialog_instance.category_combo.currentIndexChanged.disconnect(
            dialog_instance.update_conditional_fields
        )
    except TypeError:
        pass  # Signal was not connected
    try:
        dialog_instance.assessment_status_combo.currentTextChanged.disconnect(
            dialog_instance.on_assessment_status_changed
        )
    except TypeError:
        pass  # Signal was not connected
    try:
        dialog_instance.lc_status_combo.currentTextChanged.disconnect(
            dialog_instance.on_lc_status_changed
        )
    except TypeError:
        pass  # Signal was not connected

    # Performance optimization: Cache frequently accessed data
    dialog_instance._cached_responsibility_name = None
    dialog_instance._cached_category_name = None
    dialog_instance._cached_category_settings = None

    # Set responsibility with caching
    if (
        not hasattr(dialog_instance, "_cached_responsibility_name")
        or dialog_instance._cached_responsibility_name is None
    ):
        resp = next(
            (
                r
                for r in dialog_instance.responsibilities
                if r["id"] == dialog_instance.case_data[12]
            ),
            None,
        )
        if resp:
            dialog_instance._cached_responsibility_name = resp["name"]
            dialog_instance.selected_responsibility_id = dialog_instance.case_data[
                12
            ]  # Set the ID for saving
    if dialog_instance._cached_responsibility_name:
        dialog_instance.responsibility_edit.setText(
            dialog_instance._cached_responsibility_name
        )

    # Set dates
    if dialog_instance.case_data[2]:  # date_incurred
        dialog_instance.date_incurred_edit.setDate(
            QDate.fromString(dialog_instance.case_data[2], "yyyy-MM-dd")
        )
    if dialog_instance.case_data[3]:  # date_identified
        dialog_instance.date_identified_edit.setDate(
            QDate.fromString(dialog_instance.case_data[3], "yyyy-MM-dd")
        )
    if dialog_instance.case_data[4]:  # date_reported
        dialog_instance.date_reported_edit.setDate(
            QDate.fromString(dialog_instance.case_data[4], "yyyy-MM-dd")
        )

    # Set description
    if dialog_instance.case_data[5]:  # description
        dialog_instance.description_edit.setPlainText(dialog_instance.case_data[5])

    # Set category
    if dialog_instance.case_data[11]:  # category
        dialog_instance.category_combo.setCurrentText(dialog_instance.case_data[11])

    # Parse evidence_paths JSON early to ensure evidence link is available for conditional fields
    evidence_paths_json = (
        dialog_instance.case_data[18] if len(dialog_instance.case_data) > 18 else None
    )  # Corrected index for evidence_paths column
    if evidence_paths_json:
        try:
            dialog_instance.evidence_paths = json.loads(evidence_paths_json)
            # Set the assessment evidence edit text so the View button works
            dialog_instance.assessment_evidence_edit.setText(
                dialog_instance.evidence_paths.get("assessment", "")
            )
        except json.JSONDecodeError:
            print(
                f"Warning: Failed to parse evidence_paths for case {dialog_instance.base_transaction_no}"
            )
            dialog_instance.evidence_paths = {}
    else:
        print(
            f"LOG: No evidence_paths found for case {dialog_instance.base_transaction_no}"
        )
        dialog_instance.evidence_paths = {}

    print(
        f"DEBUG: Loaded assessment evidence: {dialog_instance.evidence_paths.get('assessment', 'None')}"
    )

    # Fallback to legacy evidence_path column if evidence_paths is empty (corrected index)
    # Do not set text on load to show placeholders
    # if not dialog_instance.evidence_paths.get('assessment') and len(dialog_instance.case_data) > 19 and dialog_instance.case_data[19]:
    #     dialog_instance.evidence_edit.setText(dialog_instance.case_data[19])

    # Explicitly clear the assessment evidence field if no valid path is found
    if not dialog_instance.evidence_paths.get("assessment") and not (
        len(dialog_instance.case_data) > 15 and dialog_instance.case_data[15]
    ):
        pass  # Do not set text to allow placeholders

    # Update conditional fields first to populate status combo with correct items
    dialog_instance.update_conditional_fields()

    # Set assessment status
    if len(dialog_instance.case_data) > 20 and dialog_instance.case_data[20]:
        dialog_instance.assessment_status = str(dialog_instance.case_data[20])
    else:
        dialog_instance.assessment_status = "Alleged"

    # Set assessment status combo
    dialog_instance.assessment_status_combo.setCurrentText(
        dialog_instance.assessment_status or "Alleged"
    )

    # Set LC status
    if (
        hasattr(dialog_instance, "lc_status_combo")
        and len(dialog_instance.case_data) > 21
        and dialog_instance.case_data[21]
    ):
        lc_status_value = str(dialog_instance.case_data[21])
        dialog_instance.lc_status_combo.setCurrentText(lc_status_value)
        dialog_instance.lc_status = lc_status_value

    # Set LC Committee Date
    if hasattr(dialog_instance, 'lc_committee_date_edit') and dialog_instance.lc_committee_date:
        try:
            date_obj = QDate.fromString(dialog_instance.lc_committee_date, "yyyy-MM-dd")
            if date_obj.isValid():
                dialog_instance.lc_committee_date_edit.setDate(date_obj)
        except Exception as e:
            print(f"Error loading LC committee date: {e}")

    # Set list and status display after conditional updates using shared logic with ViewCasesDialog
    # Use workflow_utils for consistent display logic
    workflow_status = dialog_instance.workflow_status_cache
    # List and Status information is now handled by the List Status Information group
    # No need to set display values since those fields were removed

    # Check if case is finalized and disable editing if so
    if dialog_instance.is_finalized:
        dialog_instance.setWindowTitle(
            f"Edit Case Details - {dialog_instance.list_name} (FINALIZED)"
        )
        # Disable all input fields for finalized cases
        dialog_instance.description_edit.setReadOnly(True)
        dialog_instance.amount_edit.setReadOnly(True)
        dialog_instance.date_incurred_edit.setReadOnly(True)
        dialog_instance.date_identified_edit.setReadOnly(True)
        dialog_instance.date_reported_edit.setReadOnly(True)
        dialog_instance.assessment_status_combo.setEnabled(False)
        dialog_instance.lc_status_combo.setEnabled(False)
        dialog_instance.assessment_evidence_edit.setReadOnly(True)
        dialog_instance.evidence_button.setEnabled(False)
        dialog_instance.bas_payment_no_edit.setReadOnly(True)
        dialog_instance.bas_payment_date_edit.setReadOnly(True)
        dialog_instance.bas_payment_date_button.setEnabled(False)
        dialog_instance.bas_journal_no_edit.setReadOnly(True)
        dialog_instance.bas_journal_date_edit.setReadOnly(True)
        dialog_instance.bas_journal_date_button.setEnabled(False)
        dialog_instance.persal_no_edit.setReadOnly(True)
        dialog_instance.minutes_edit.setReadOnly(True)
        dialog_instance.minutes_button.setEnabled(False)
        dialog_instance.source_doc_edit.setReadOnly(True)
        dialog_instance.source_doc_button.setEnabled(False)
        dialog_instance.supporting_evidence_edit.setReadOnly(True)
        dialog_instance.supporting_evidence_button.setEnabled(False)
        dialog_instance.recovery_evidence_edit.setReadOnly(True)
        dialog_instance.recovery_evidence_button.setEnabled(False)
        dialog_instance.criminal_charges_combo.setEnabled(False)
        dialog_instance.disciplinary_combo.setEnabled(False)
        dialog_instance.prevention_steps_edit.setReadOnly(True)

        # Disable save button for finalized cases
        dialog_instance.save_button.setEnabled(False)
        dialog_instance.save_button.setText("Case Finalized - No Changes Allowed")

        # Add finalization notice
        finalization_reason = "Case has been finalized"  # Default reason since we don't have this field in the current schema
        finalization_label = QLabel(f"Finalized: {finalization_reason}")
        finalization_label.setStyleSheet(
            "color: #d32f2f; font-weight: bold; font-size: 15px; margin-top: 10px;"
        )
        dialog_instance.main_layout.insertWidget(0, finalization_label)

    # Set criminal charges
    if len(dialog_instance.case_data) > 22 and dialog_instance.case_data[22]:
        dialog_instance.criminal_charges_combo.setCurrentText(
            dialog_instance.case_data[22]
        )

    # Set disciplinary
    if len(dialog_instance.case_data) > 23 and dialog_instance.case_data[23]:
        dialog_instance.disciplinary_combo.setCurrentText(dialog_instance.case_data[23])

    # Set loss recovery (now handled by recovery progress system)
    # The loss recovery status is now auto-managed based on installment data
    # No need to set it manually as it's calculated from installments table

    # Set prevention steps
    if len(dialog_instance.case_data) > 25 and dialog_instance.case_data[25]:
        dialog_instance.prevention_steps_edit.setPlainText(
            dialog_instance.case_data[25]
        )

    # Set amount
    if dialog_instance.case_data[13]:  # amount
        dialog_instance.amount_edit.setText(str(dialog_instance.case_data[13]))

    # Set remaining evidence paths (recovery, lc_minutes, supporting, source) from evidence_paths or fallback columns
    if hasattr(dialog_instance, "evidence_paths") and dialog_instance.evidence_paths:
        if "recovery" in dialog_instance.evidence_paths:
            dialog_instance.recovery_evidence_edit.setText(
                dialog_instance.evidence_paths["recovery"]
            )
        if "lc_minutes" in dialog_instance.evidence_paths:
            dialog_instance.minutes_edit.setText(
                dialog_instance.evidence_paths["lc_minutes"]
            )
        # Do not set text on load to show placeholders
        # if 'supporting' in dialog_instance.evidence_paths:
        #     dialog_instance.supporting_evidence_edit.setText(dialog_instance.evidence_paths.get('supporting', ''))
        if "source" in dialog_instance.evidence_paths:
            dialog_instance.source_doc_edit.setText(
                dialog_instance.evidence_paths["source"]
            )
    else:
        # Fallback to old columns if evidence_paths is not set
        # Note: File paths are now stored in evidence_paths JSON, so these fallbacks are not needed
        pass

    # Load source_document from database column if not loaded from evidence_paths
    if (
        len(dialog_instance.case_data) > 14
        and dialog_instance.case_data[14]
        and not dialog_instance.source_doc_edit.text().strip()
    ):
        dialog_instance.source_doc_edit.setText(dialog_instance.case_data[14])

    # Set Loss Control fields - use lc_status
    if dialog_instance.lc_status:
        # Update recovery evidence visibility, LC Minutes placeholder, and list status grid based on status

        # First, reset all statuses to N/A
        dialog_instance.update_list_status_grid("Recovery in Progress", "N/A")
        dialog_instance.update_list_status_grid("Recovered", "N/A")
        dialog_instance.update_list_status_grid("Write-Off Recommended", "N/A")

        status = dialog_instance.lc_status
        if status == "Recovery in Progress":
            # Show recovery group
            if hasattr(dialog_instance, "recovery_group"):
                dialog_instance.recovery_group.setVisible(True)
            
            # Initialize recovery progress
            from scripts.ui.dialogs.edit_case.edit_case_handlers import update_recovery_progress
            update_recovery_progress(dialog_instance)
            
            # Show recovery fields for installment tracking
            if hasattr(dialog_instance, 'debtor_name_edit'):
                dialog_instance.debtor_name_edit.setVisible(True)
            if hasattr(dialog_instance, 'debtor_number_edit'):
                dialog_instance.debtor_number_edit.setVisible(True)
            if hasattr(dialog_instance, 'debt_number_edit'):
                dialog_instance.debt_number_edit.setVisible(True)
            
            # Hide Loss Control Committee recovery evidence, show Recovery in Progress recovery evidence
            dialog_instance.recovery_evidence_label.setVisible(False)
            dialog_instance.recovery_evidence_edit.setVisible(False)
            dialog_instance.recovery_evidence_button.setVisible(False)
            dialog_instance.recovery_evidence_view_button.setVisible(False)
            
            # Show Recovery in Progress recovery evidence
            if hasattr(dialog_instance, 'recovery_evidence_rip_label'):
                dialog_instance.recovery_evidence_rip_label.setVisible(True)
            if hasattr(dialog_instance, 'recovery_evidence_rip_edit'):
                dialog_instance.recovery_evidence_rip_edit.setVisible(True)
                dialog_instance.recovery_evidence_rip_edit.setPlaceholderText("Upload latest Debt Inquiry report")
            if hasattr(dialog_instance, 'recovery_evidence_rip_button'):
                dialog_instance.recovery_evidence_rip_button.setVisible(True)
            if hasattr(dialog_instance, 'recovery_evidence_rip_view_button'):
                dialog_instance.recovery_evidence_rip_view_button.setVisible(True)
            
            dialog_instance.minutes_edit.setPlaceholderText(
                "Loss Control Minutes are REQUIRED"
            )
            # Update List Status Information grid
            dialog_instance.update_list_status_grid("Recovery in Progress", "Recovery in Progress")
            
        elif status == "Recovered":
            # Hide installment fields, show only total recovered
            if hasattr(dialog_instance, 'debtor_name_edit'):
                dialog_instance.debtor_name_edit.setVisible(False)
            if hasattr(dialog_instance, 'debtor_number_edit'):
                dialog_instance.debtor_number_edit.setVisible(False)
            if hasattr(dialog_instance, 'debt_number_edit'):
                dialog_instance.debt_number_edit.setVisible(False)
            
            # Show Loss Control Committee recovery evidence, hide Recovery in Progress recovery evidence
            dialog_instance.recovery_evidence_label.setVisible(True)
            dialog_instance.recovery_evidence_edit.setVisible(True)
            dialog_instance.recovery_evidence_button.setVisible(True)
            dialog_instance.recovery_evidence_view_button.setVisible(True)
            
            # Hide Recovery in Progress recovery evidence
            if hasattr(dialog_instance, 'recovery_evidence_rip_label'):
                dialog_instance.recovery_evidence_rip_label.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_rip_edit'):
                dialog_instance.recovery_evidence_rip_edit.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_rip_button'):
                dialog_instance.recovery_evidence_rip_button.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_rip_view_button'):
                dialog_instance.recovery_evidence_rip_view_button.setVisible(False)
            
            dialog_instance.minutes_edit.setPlaceholderText(
                "Loss Control Minutes are REQUIRED"
            )
            # Update List Status Information grid
            dialog_instance.update_list_status_grid("Recovered", "Recovered")
            
        elif status == "Write Off Recommended":
            # Hide all recovery fields
            if hasattr(dialog_instance, 'debtor_name_edit'):
                dialog_instance.debtor_name_edit.setVisible(False)
            if hasattr(dialog_instance, 'debtor_number_edit'):
                dialog_instance.debtor_number_edit.setVisible(False)
            if hasattr(dialog_instance, 'debt_number_edit'):
                dialog_instance.debt_number_edit.setVisible(False)
            
            dialog_instance.recovery_evidence_label.setVisible(False)
            dialog_instance.recovery_evidence_edit.setVisible(False)
            dialog_instance.recovery_evidence_button.setVisible(False)
            dialog_instance.recovery_evidence_view_button.setVisible(False)
            dialog_instance.recovery_evidence_edit.clear()
            dialog_instance.minutes_edit.setPlaceholderText(
                "Loss Control Minutes are REQUIRED"
            )
            # Update List Status Information grid
            dialog_instance.update_list_status_grid(
                "Write-Off Recommended", "Write Off Recommended"
            )
        else:
            # Hide all recovery fields for other statuses
            if hasattr(dialog_instance, 'debtor_name_edit'):
                dialog_instance.debtor_name_edit.setVisible(False)
            if hasattr(dialog_instance, 'debtor_number_edit'):
                dialog_instance.debtor_number_edit.setVisible(False)
            if hasattr(dialog_instance, 'debt_number_edit'):
                dialog_instance.debt_number_edit.setVisible(False)
            
            if hasattr(dialog_instance, 'recovery_evidence_label'):
                dialog_instance.recovery_evidence_label.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_edit'):
                dialog_instance.recovery_evidence_edit.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_button'):
                dialog_instance.recovery_evidence_button.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_view_button'):
                dialog_instance.recovery_evidence_view_button.setVisible(False)
            if hasattr(dialog_instance, 'recovery_evidence_edit'):
                dialog_instance.recovery_evidence_edit.clear()
            if hasattr(dialog_instance, 'minutes_edit'):
                dialog_instance.minutes_edit.setPlaceholderText("")

    # Set recovery fields with proper type conversion and null checking
    # Clear any weird placeholder values and only set valid data
    if len(dialog_instance.case_data) > 30:  # debtor_name
        debtor_name = dialog_instance.case_data[30]
        if debtor_name is not None and str(debtor_name).strip() and str(debtor_name) not in ['7', '149', '-LS,-RIP']:
            dialog_instance.debtor_name_edit.setText(str(debtor_name).strip())
        else:
            dialog_instance.debtor_name_edit.clear()
    
    if len(dialog_instance.case_data) > 31:  # debt_number
        debt_number = dialog_instance.case_data[31]
        if debt_number is not None and str(debt_number).strip() and str(debt_number) not in ['7', '149', '-LS,-RIP']:
            dialog_instance.debt_number_edit.setText(str(debt_number).strip())
        else:
            dialog_instance.debt_number_edit.clear()
    
    # Initialize recovery progress display (this will calculate actual values from installments table)
    if hasattr(dialog_instance, 'recovery_group') and dialog_instance.recovery_group.isVisible():
        from scripts.ui.dialogs.edit_case.edit_case_handlers import update_recovery_progress
        update_recovery_progress(dialog_instance)
    
    # Note: Old installment fields are no longer used in the new UI structure
    # Installment data is now managed through the installments table

    # Set BAS fields
    if dialog_instance.case_data[6]:  # bas_payment_no
        dialog_instance.bas_payment_no_edit.setText(dialog_instance.case_data[6])
    if dialog_instance.case_data[7]:  # bas_payment_date
        dialog_instance.bas_payment_date_edit.setText(dialog_instance.case_data[7])
    else:
        dialog_instance.bas_payment_date_edit.clear()  # Clear date if NULL

    # Set BAS Journal fields
    if (
        len(dialog_instance.case_data) > 8 and dialog_instance.case_data[8]
    ):  # bas_journal_no
        dialog_instance.bas_journal_no_edit.setText(dialog_instance.case_data[8])
    if (
        len(dialog_instance.case_data) > 9 and dialog_instance.case_data[9]
    ):  # bas_journal_date
        dialog_instance.bas_journal_date_edit.setText(dialog_instance.case_data[9])
    else:
        dialog_instance.bas_journal_date_edit.clear()  # Clear date if NULL

    # Set Persal No
    if dialog_instance.case_data[10]:  # persal_no
        dialog_instance.persal_no_edit.setText(dialog_instance.case_data[10])

    # File paths are now handled through evidence_paths JSON above
    # No need for additional fallback logic here

    # Update list status display after loading all data
    update_list_status_display(dialog_instance)

    # Reconnect signals
    dialog_instance.category_combo.currentIndexChanged.connect(
        dialog_instance.schedule_update_conditional_fields
    )
    dialog_instance.assessment_status_combo.currentTextChanged.connect(
        dialog_instance.on_assessment_status_changed
    )
    dialog_instance.lc_status_combo.currentTextChanged.connect(
        dialog_instance.on_lc_status_changed
    )

    # Set placeholders after loading text
    dialog_instance.update_conditional_fields()


# End of File
