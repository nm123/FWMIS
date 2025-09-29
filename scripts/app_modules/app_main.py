"""
Main FWMIS Application Module

The main application class for the Fruitless and Wasteful Expenditure Management
Information System. This module has been refactored from the monolithic fw_management.py
into focused, maintainable modules.
"""

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMainWindow, QMessageBox

from .action_handlers.admin_actions import *
from .action_handlers.case_actions import *
from .action_handlers.management_actions import *
from .action_handlers.view_actions import *

# Import our modular components
from .app_imports import *
from .menu_setup import setup_menu
from .ui_setup import setup_ui


class FWManagementApp(QMainWindow):
    """
    Main application window for the FWMIS system.

    This class manages the overall application lifecycle, UI setup, and menu actions.
    """

    def __init__(self):
        """Initialize the FWMIS application."""
        super().__init__()
        self.setWindowTitle(
            "FWMIS - Fruitless and Wasteful Expenditure Management Information System"
        )

        # Set minimum size and allow resizing/maximizing
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)  # Default size
        self.center_window()

        # Enable maximize button and window resizing
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )

        # Apply professional theme
        apply_theme(self)

        # Initialize database tables
        try:
            from scripts.Utilities.list_utils import load_lists
            from scripts.Utilities.financial_utils import get_all_financial_years

            load_lists()  # Initialize core tables including financial_years
            initialize_shared_documents_table()

            # Initialize default financial years if none exist
            if not get_all_financial_years():
                self._initialize_default_financial_years()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Database Warning",
                f"Failed to initialize database tables: {str(e)}",
            )

        self.setup_ui()
        self.setup_menu()

    def center_window(self) -> None:
        """Center the window on the screen."""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

    def setup_ui(self) -> None:
        """Set up the main user interface."""
        setup_ui(self)

    def setup_menu(self) -> None:
        """Set up the main menu bar."""
        setup_menu(self)

    def create_menu_action(self, text: str, handler) -> QAction:
        """
        Create a menu action with the given text and handler.

        Args:
            text: The menu item text
            handler: The function to call when the action is triggered

        Returns:
            QAction: The created menu action
        """
        action = QAction(text, self)
        action.triggered.connect(handler)
        return action

    def refresh_cases(self) -> None:
        """Refresh the cases display."""
        # This method can be implemented if needed for refreshing views
        pass

    # Import all action handlers as methods
    add_new_case = add_new_case
    import_undisclosed_cases = import_undisclosed_cases
    view_cases = view_cases
    manage_cases = manage_cases
    todo_list = todo_list
    view_checklist = view_checklist
    view_lead_schedule = view_lead_schedule
    view_deleted_items = view_deleted_items
    view_deleted_cases = view_deleted_cases
    manage_categories = manage_categories
    manage_lists = manage_lists
    manage_responsibilities = manage_responsibilities
    manage_email_templates = manage_email_templates
    manage_financial_years = manage_financial_years
    manage_write_off_delegations = manage_write_off_delegations
    wipe_cases = wipe_cases
    open_write_off_annexures = open_write_off_annexures
    open_write_off_management = open_write_off_management
    create_write_off_submission = create_write_off_submission
    open_finalization_dashboard = open_finalization_dashboard
    open_optimization_management = open_optimization_management
    open_database_archiving = open_database_archiving
    open_automated_testing = open_automated_testing
    run_daily_test_verification = run_daily_test_verification
    generate_reports = generate_reports

    def run_verification_auto_fix(
        self, parent_dialog: Optional[QMainWindow] = None
    ) -> None:
        """
        Run verification auto-fix functionality.

        Args:
            parent_dialog: Parent dialog for the verification process
        """
        try:
            # Import here to avoid circular imports
            from scripts.daily_test_check import run_verification_auto_fix

            run_verification_auto_fix(parent_dialog or self)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to run verification auto-fix: {str(e)}"
            )

    def _initialize_default_financial_years(self) -> None:
        """
        Initialize default financial years if none exist.
        Creates financial years starting from 2019-2020 onwards.
        South African financial years run from April to March.
        """
        try:
            import sqlite3
            from datetime import date
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create financial years from 2019-2020 to current year + 2
            # South African financial years: April (start_year) to March (end_year)
            current_year = date.today().year

            financial_years = []
            for start_year in range(2019, current_year + 3):  # 2019 to current + 2
                end_year = start_year + 1
                fy_string = f"{start_year}-{(end_year) % 100:02d}"

                # Determine status and active period
                if start_year == current_year:
                    status = 'open'
                    active_period = 1  # Current year is active
                elif start_year > current_year:
                    status = 'open'  # Future years
                    active_period = None
                else:
                    status = 'closed'  # Past years
                    active_period = None

                financial_years.append((start_year, end_year, status, active_period))

            # Insert default financial years
            cursor.executemany(
                """
                INSERT OR IGNORE INTO financial_years
                (start_year, end_year, status, active_period)
                VALUES (?, ?, ?, ?)
                """,
                financial_years
            )

            conn.commit()
            conn.close()

            fy_strings = [f"{fy[0]}-{(fy[1]) % 100:02d}" for fy in financial_years]
            print(f"Initialized default financial years: {', '.join(fy_strings)}")
            print("Note: Opening balance for 1 April 2019 was 0.00")

        except Exception as e:
            print(f"Failed to initialize default financial years: {e}")


def exception_handler(exctype, value, traceback):
    """
    Global exception handler for the application.

    Args:
        exctype: Exception type
        value: Exception value
        traceback: Exception traceback
    """
    import sys
    import traceback as tb

    error_msg = "".join(tb.format_exception(exctype, value, traceback))
    print(f"Unhandled exception: {error_msg}")

    # Show error dialog to user
    from PyQt5.QtWidgets import QApplication, QMessageBox

    if QApplication.instance():
        QMessageBox.critical(
            None,
            "Critical Error",
            f"An unexpected error occurred:\n\n{str(value)}\n\nPlease restart the application.",
        )

    sys.exit(1)
