"""
Financial Year Management Dialog Module

Main dialog class for financial year and period management, refactored into modular components.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTreeWidgetItem


class FinancialYearManagementDialog:
    """
    Main dialog for managing financial years and periods.

    This dialog provides comprehensive functionality for creating, opening, and closing
    financial years, as well as managing their constituent periods.
    """

    def __init__(self, parent=None):
        """
        Initialize the financial year management dialog.
        
        Args:
            parent: Parent widget
        """
        from PyQt5.QtWidgets import QDialog

        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Manage Financial Years & Periods")
        self.dialog.setFixedSize(900, 700)

        # Initialize managers
        from .fy_manager import FinancialYearManager
        from .period_manager import PeriodManager
        from .ui_setup import UISetupManager
        
        from scripts.Utilities.central_fy_utils import CentralFYUtils, FYError
        from scripts.Utilities.config import DB_PATH
        from PyQt5.QtWidgets import QMessageBox
        
        self.utils = CentralFYUtils(DB_PATH)

        self.ui_manager = UISetupManager(self)
        self.fy_manager = FinancialYearManager(self)
        self.period_manager = PeriodManager(self)

        # Setup UI and load data
        self.ui_manager.setup_ui()
        self.load_financial_years()

    # Delegate UI setup methods
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.ui_manager.setup_ui()

    # Delegate financial year methods
    def load_financial_years(self) -> None:
        """Load financial years."""
        self.fy_manager.load_financial_years()

    def create_financial_year(self) -> None:
        """Create a new financial year."""
        self.fy_manager.create_financial_year()

    def on_activate_clicked(self):
        current_item = self.fy_tree.currentItem()
        if current_item:
            try:
                self.utils.activate_fy(current_item.fy_id)
            except FYError as e:
                QMessageBox.warning(self.dialog, "FY Error", str(e))

    def on_close_clicked(self):
        current_item = self.fy_tree.currentItem()
        if current_item:
            try:
                self.utils.close_fy(current_item.fy_id)
            except FYError as e:
                QMessageBox.warning(self.dialog, "FY Error", str(e))

    def open_financial_year(self) -> None:
        """Open a financial year."""
        self.fy_manager.open_financial_year()

    def close_financial_year(self) -> None:
        """Close a financial year."""
        self.fy_manager.close_financial_year()

    # Delegate period methods
    def load_periods(self, fy_id: int) -> None:
        """
        Load periods for a financial year.

        Args:
            fy_id: Financial year ID
        """
        self.period_manager.load_periods(fy_id)

    def open_period(self) -> None:
        """Open a period."""
        self.period_manager.open_period()

    def close_period(self) -> None:
        """Close a period."""
        self.period_manager.close_period()

    def validate_period_12_closure(self, period_id: int) -> bool:
        """
        Validate period 12 closure.

        Args:
            period_id: Period ID

        Returns:
            bool: True if validation passes
        """
        return self.period_manager.validate_period_12_closure(period_id)

    def can_open_period_13(self, fy_id: int) -> bool:
        """
        Check if period 13 can be opened.

        Args:
            fy_id: Financial year ID

        Returns:
            bool: True if period 13 can be opened
        """
        return self.period_manager.can_open_period_13(fy_id)

    # Event handlers
    def on_fy_select(self) -> None:
        """Handle financial year selection."""
        current_item = self.fy_tree.currentItem()
        if current_item:
            self.load_periods(current_item.fy_id)
            self.status_label.setText(
                f"Selected: {current_item.fy_string} ({'Open' if current_item.is_open else 'Closed'})"
            )
        else:
            self.periods_tree.clear()
            self.status_label.setText("")

    def update_status(self, fy_id: int, fy_status: str) -> None:
        """
        Update the status display.

        Args:
            fy_id: Financial year ID
            fy_status: Status string
        """
        self.status_label.setText(f"Financial Year {fy_id}: {fy_status}")

    def exec_(self):
        """Execute the dialog."""
        return self.dialog.exec_()
