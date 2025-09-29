"""
Case Action Handlers

Contains action handlers for case-related operations in the main FWMIS application.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_main import FWManagementApp


def add_new_case(app: "FWManagementApp") -> None:
    """Handle adding a new case."""
    try:
        from scripts.case_management import AddNewCaseDialog

        dialog = AddNewCaseDialog(app)
        dialog.exec_()
        app.refresh_cases()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Add New Case dialog: {str(e)}"
        )


def import_undisclosed_cases(app: "FWManagementApp") -> None:
    """Handle importing undisclosed cases."""
    try:
        from scripts.ui.dialogs.import_cases_dialog import import_undisclosed_cases

        import_undisclosed_cases(app)
        app.refresh_cases()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Import Undisclosed Cases dialog: {str(e)}"
        )


def view_cases(app: "FWManagementApp") -> None:
    """Handle viewing cases."""
    try:
        from scripts.case_management import ViewCasesDialog

        dialog = ViewCasesDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open View Cases dialog: {str(e)}"
        )


def manage_cases(app: "FWManagementApp") -> None:
    """Handle managing/editing cases."""
    try:
        from scripts.case_management import EditCasesDialog

        dialog = EditCasesDialog(app)
        dialog.exec_()
        app.refresh_cases()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Edit Cases dialog: {str(e)}"
        )


def todo_list(app: "FWManagementApp") -> None:
    """Handle viewing the to-do list."""
    try:
        from scripts.case_management import ToDoListDialog

        dialog = ToDoListDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open To-Do List dialog: {str(e)}"
        )
