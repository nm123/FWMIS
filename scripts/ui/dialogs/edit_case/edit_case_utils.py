import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.workflow_utils import get_display_transaction_no
from scripts.case_management_modules.determination_dialog import DeterminationDialog

def delete_case(dialog_instance):
    """Delete case by moving it to Deleted Cases"""
    display_no = get_display_transaction_no(dialog_instance.base_transaction_no, dialog_instance.suffixes)
    reply = QMessageBox.question(
        dialog_instance, "Confirm Delete",
        f"Are you sure you want to delete case {display_no}?\n\n"
        "This will move the case to the Deleted Cases list.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Update case to add -DEL suffix and mark as deleted
            new_suffixes = dialog_instance.suffixes
            if new_suffixes:
                new_suffixes += ",-DEL"
            else:
                new_suffixes = "-DEL"

            cursor.execute("""
                UPDATE cases
                SET suffixes = ?
                WHERE id = ?
            """, (new_suffixes, dialog_instance.case_id))

            conn.commit()
            conn.close()

            # Log audit trail
            save_audit_log("delete_case", {
                "timestamp": datetime.now().isoformat(),
                "case_id": dialog_instance.case_id,
                "base_transaction_no": dialog_instance.base_transaction_no,
                "details": "Case marked as deleted with -DEL suffix"
            }, dialog_instance.fy)

            QMessageBox.information(dialog_instance, "Success", f"Case {display_no} has been moved to Deleted Cases.")
            dialog_instance.case_modified.emit()  # Signal parent to refresh
            dialog_instance.accept()

        except Exception as e:
            QMessageBox.critical(dialog_instance, "Error", f"Failed to delete case: {str(e)}")

def open_determination_dialog(dialog_instance):
    """Open the Loss Control Committee determination dialog"""
    try:
        dialog = DeterminationDialog(dialog_instance.case_data, dialog_instance)
        if dialog.exec_():
            # Refresh the current dialog data if determination was saved
            QMessageBox.information(dialog_instance, "Determination Complete",
                                  "Determination has been recorded. Please save the case to apply any status changes.")
    except Exception as e:
        QMessageBox.critical(dialog_instance, "Error", f"Failed to open determination dialog: {str(e)}")

def update_determination_button_visibility(dialog_instance):
    """Update the visibility of the determination button based on case status"""
    try:
        selected_assessment_status = dialog_instance.assessment_status_combo.currentText()

        # Show determination button for Confirmed cases that appear in Lead Schedule
        # (have -LS suffix) and haven't been through LC determination yet
        show_determination = (selected_assessment_status == "Confirmed" and
                            "-LS" in dialog_instance.suffixes and
                            (not dialog_instance.lc_status or dialog_instance.lc_status == "Awaiting LC determination"))

        if hasattr(dialog_instance, 'determination_button'):
            dialog_instance.determination_button.setVisible(show_determination)

    except Exception as e:
        print(f"Warning: Error updating determination button visibility: {e}")
        if hasattr(dialog_instance, 'determination_button'):
            dialog_instance.determination_button.setVisible(False)

def schedule_update_conditional_fields(dialog_instance):
    """Schedule a debounced update of conditional fields to prevent excessive calls"""
    dialog_instance.update_timer.start(150)  # 150ms debounce delay

# End of File