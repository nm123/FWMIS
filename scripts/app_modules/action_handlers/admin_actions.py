"""
Administrative Action Handlers

Contains action handlers for administrative operations in the main FWMIS application.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_main import FWManagementApp


def wipe_cases(app: "FWManagementApp") -> None:
    """Handle wiping cases (dangerous operation)."""
    try:
        from scripts.wipe_cases_dialog import WipeCasesDialog

        dialog = WipeCasesDialog(app)
        dialog.exec_()
        app.refresh_cases()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Wipe Cases dialog: {str(e)}"
        )


def open_write_off_annexures(app: "FWManagementApp") -> None:
    """Handle opening write-off annexure management."""
    try:
        from scripts.ui.dialogs.annexure_preparation_dialog import (
            AnnexurePreparationDialog,
        )

        dialog = AnnexurePreparationDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Write-Off Annexures dialog: {str(e)}"
        )


def open_write_off_management(app: "FWManagementApp") -> None:
    """Handle opening write-off management."""
    try:
        from scripts.case_management_modules.write_off_management_dialog import (
            WriteOffManagementDialog,
        )

        dialog = WriteOffManagementDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Write-Off Management dialog: {str(e)}"
        )


def create_write_off_submission(app: "FWManagementApp") -> None:
    """Handle creating write-off submission."""
    try:
        from scripts.case_management_modules.write_off_submission_dialog import (
            WriteOffSubmissionDialog,
        )

        dialog = WriteOffSubmissionDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Write-Off Submission dialog: {str(e)}"
        )


def open_finalization_dashboard(app: "FWManagementApp") -> None:
    """Handle opening finalization dashboard."""
    try:
        from scripts.ui.dialogs.finalization_dashboard_dialog import (
            FinalizationDashboardDialog,
        )

        dialog = FinalizationDashboardDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Finalization Dashboard: {str(e)}"
        )


def open_optimization_management(app: "FWManagementApp") -> None:
    """Handle opening optimization management."""
    try:
        from scripts.optimization_management import open_optimization_management

        open_optimization_management(app)
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Optimization Management: {str(e)}"
        )


def open_database_archiving(app: "FWManagementApp") -> None:
    """Handle opening database archiving management."""
    try:
        from scripts.ui.dialogs.database_archiving_dialog import DatabaseArchivingDialog

        dialog = DatabaseArchivingDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Database Archiving dialog: {str(e)}"
        )


def open_automated_testing(app: "FWManagementApp") -> None:
    """Handle opening automated testing management."""
    try:
        from scripts.ui.dialogs.automated_testing_dialog import show_automated_testing_dialog

        show_automated_testing_dialog(app)
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Automated Testing dialog: {str(e)}"
        )


def run_daily_test_verification(app: "FWManagementApp") -> None:
    """Handle running daily test verification."""
    try:
        app.run_verification_auto_fix(app)
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to run daily test verification: {str(e)}"
        )


def generate_reports(app: "FWManagementApp") -> None:
    """Handle generating reports."""
    try:
        from scripts.report_management import ReportManagementDialog

        dialog = ReportManagementDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Report Management dialog: {str(e)}"
        )
