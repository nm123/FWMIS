"""
View Action Handlers

Contains action handlers for view-related operations in the main FWMIS application.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_main import FWManagementApp


def view_checklist(app: "FWManagementApp") -> None:
    """Handle viewing the checklist."""
    try:
        from scripts.ui.dialogs.checklist_dialog import ChecklistDialog

        dialog = ChecklistDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(app, "Error", f"Failed to open Checklist dialog: {str(e)}")


def view_lead_schedule(app: "FWManagementApp") -> None:
    """Handle viewing the lead schedule."""
    try:
        from scripts.ui.dialogs.checklist_dialog import ChecklistDialog

        dialog = ChecklistDialog(app, list_type="Lead Schedule")
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Lead Schedule dialog: {str(e)}"
        )


def view_deleted_items(app: "FWManagementApp") -> None:
    """Handle viewing deleted items."""
    try:
        from scripts.case_management import ViewDeletedCasesDialog

        dialog = ViewDeletedCasesDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Deleted Items dialog: {str(e)}"
        )


def view_deleted_cases(app: "FWManagementApp") -> None:
    """Handle viewing deleted cases."""
    try:
        from scripts.case_management import ViewDeletedCasesDialog

        dialog = ViewDeletedCasesDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Deleted Cases dialog: {str(e)}"
        )
