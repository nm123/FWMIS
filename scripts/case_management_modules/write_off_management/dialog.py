"""
Write-Off Management Dialog Module

Main dialog class for write-off management, refactored into modular components.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

from PyQt5.QtWidgets import QDialog

from .annexure_manager import AnnexureManager
from .ui_setup import UISetupManager


class WriteOffManagementDialog(QDialog):
    """
    Main dialog for write-off annexure management.

    This dialog provides comprehensive functionality for managing write-off
    annexures, including approval workflows and exports.
    """

    def __init__(self, parent: Optional["QWidget"] = None) -> None:
        """
        Initialize the write-off management dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize managers
        self.ui_manager = UISetupManager(self)
        self.annexure_manager = AnnexureManager(self)

        # Get current financial year
        from scripts.Utilities.financial_utils import get_financial_year

        self.fy = get_financial_year()

        # Setup UI
        self.ui_manager.setup_ui()

        # Load initial data
        self.load_annexures()

    # Delegate UI setup methods
    def setup_ui(self) -> None:
        """Set up the main dialog UI."""
        self.ui_manager.setup_ui()

    # Delegate annexure management methods
    def load_annexures(self) -> None:
        """Load annexures data."""
        self.annexure_manager.load_annexures()

    def create_annexure_actions_widget(
        self, annexure_id: int, annexure_no: str
    ) -> Optional["QWidget"]:
        """
        Create action buttons widget for an annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number

        Returns:
            QWidget: Widget containing action buttons
        """
        return self.annexure_manager.create_annexure_actions_widget(
            annexure_id, annexure_no
        )

    def approve_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Approve a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        self.annexure_manager.approve_annexure(annexure_id, annexure_no)

    def decline_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Decline a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        self.annexure_manager.decline_annexure(annexure_id, annexure_no)

    def view_annexure_details(self, annexure_id: int) -> None:
        """
        View detailed information about an annexure.

        Args:
            annexure_id: The annexure ID
        """
        self.annexure_manager.view_annexure_details(annexure_id)

    def delete_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Delete a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        self.annexure_manager.delete_annexure(annexure_id, annexure_no)

    def export_annexure_excel(self, annexure_id: int, annexure_no: str) -> None:
        """
        Export annexure to Excel.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        self.annexure_manager._export_annexure_excel(annexure_id, annexure_no)

    def export_annexure_pdf(self, annexure_id: int, annexure_no: str) -> None:
        """
        Export annexure to PDF.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        self.annexure_manager._export_annexure_pdf(annexure_id, annexure_no)

    def refresh_all(self) -> None:
        """Refresh all data in the dialog."""
        self.load_annexures()
