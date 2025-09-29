"""
Management Action Handlers

Contains action handlers for management operations in the main FWMIS application.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_main import FWManagementApp


def manage_categories(app: "FWManagementApp") -> None:
    """Handle managing categories."""
    try:
        from scripts.category_management import ManageCategoriesDialog

        dialog = ManageCategoriesDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Manage Categories dialog: {str(e)}"
        )


def manage_lists(app: "FWManagementApp") -> None:
    """Handle managing lists."""
    try:
        from scripts.list_management import ManageListsDialog

        dialog = ManageListsDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Manage Lists dialog: {str(e)}"
        )


def manage_responsibilities(app: "FWManagementApp") -> None:
    """Handle managing responsibilities."""
    try:
        from scripts.responsibility_management.responsibility_management_dialog import ResponsibilityManagementDialog

        dialog = ResponsibilityManagementDialog(app)
        dialog.show()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Manage Responsibilities dialog: {str(e)}"
        )


def manage_email_templates(app: "FWManagementApp") -> None:
    """Handle managing email templates."""
    try:
        from scripts.email_template_management import ManageEmailTemplatesDialog

        dialog = ManageEmailTemplatesDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Manage Email Templates dialog: {str(e)}"
        )


def manage_financial_years(app: "FWManagementApp") -> None:
    """Handle managing financial years."""
    try:
        from scripts.financial_year_management import FinancialYearManagementDialog

        dialog = FinancialYearManagementDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app, "Error", f"Failed to open Manage Financial Years dialog: {str(e)}"
        )


def manage_write_off_delegations(app: "FWManagementApp") -> None:
    """Handle managing write-off delegations."""
    try:
        from scripts.ui.dialogs.admin.delegation_manager import DelegationManagerDialog

        dialog = DelegationManagerDialog(app)
        dialog.exec_()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            app,
            "Error",
            f"Failed to open Manage Write-Off Delegations dialog: {str(e)}",
        )
