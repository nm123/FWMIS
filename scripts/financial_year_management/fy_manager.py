"""
Financial Year Manager Module

Contains functionality for managing financial years.
"""
from scripts.Utilities.central_fy_utils import CentralFYUtils
from scripts.Utilities.config import DB_PATH

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from .dialog import FinancialYearManagementDialog


class FinancialYearManager:
    """
    Manages financial year operations.
    """

    def __init__(self, dialog: "FinancialYearManagementDialog"):
        """
        Initialize the financial year manager.

        Args:
            dialog: The parent FinancialYearManagementDialog instance
        """
        self.dialog = dialog
        self.utils = CentralFYUtils(DB_PATH)

    def load_financial_years(self) -> None:
        """
        Load financial years from database and populate the tree.
        """
        try:
            import sqlite3

            from PyQt5.QtGui import QColor
            from PyQt5.QtWidgets import QTreeWidgetItem

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if active_period column exists
            cursor.execute("PRAGMA table_info(financial_years)")
            columns = [row[1] for row in cursor.fetchall()]
            has_active_period = 'active_period' in columns

            # Get all financial years with dynamic query
            if has_active_period:
                cursor.execute(
                    """
                    SELECT id, start_year, end_year, status, active_period
                    FROM financial_years
                    ORDER BY start_year DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, start_year, end_year, status
                    FROM financial_years
                    ORDER BY start_year DESC
                    """
                )

            financial_years = cursor.fetchall()
            conn.close()

            # Clear existing items
            self.dialog.fy_tree.clear()

            # Add financial years to tree
            for row in financial_years:
                if has_active_period:
                    fy_id, start_year, end_year, status, active_period = row
                else:
                    fy_id, start_year, end_year, status = row
                    active_period = None

                fy_string = f"{start_year}-{end_year}"
                item = QTreeWidgetItem([fy_string])

                # Store data
                item.fy_id = fy_id
                item.fy_string = fy_string
                item.start_year = start_year
                item.end_year = end_year
                item.status = status
                item.active_period = active_period
                item.is_open = status == 'open'

                # Set color based on status and active period
                if active_period == 1 and status == 'open':
                    # Special highlight for truly active FY
                    item.setBackground(0, QColor(144, 238, 144))  # Light green for active
                elif status == 'open':
                    item.setBackground(0, QColor(*self.dialog.ui_manager.COLOR_OPEN))
                else:
                    item.setBackground(0, QColor(*self.dialog.ui_manager.COLOR_CLOSED))

                self.dialog.fy_tree.addTopLevelItem(item)

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None, "Error", f"Failed to load financial years: {str(e)}"
            )

    def create_financial_year(self) -> None:
        """
        Create a new financial year using auto-generation.
        """
        try:
            from PyQt5.QtWidgets import QMessageBox
    
            # Create the next FY automatically
            new_fy_id = self.create_next_fy()
            if new_fy_id is None:
                return  # Error already shown in create_next_fy
    
            # Get the new FY details for display
            import sqlite3
            from scripts.Utilities.config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT start_year, end_year FROM financial_years WHERE id = ?",
                (new_fy_id,)
            )
            result = cursor.fetchone()
            conn.close()
            if not result:
                return
    
            start_year, end_year = result
            fy_string = f"{start_year}-{end_year}"
    
            # Success message
            QMessageBox.information(
                None,
                "Success",
                f"Next financial year {fy_string} created successfully with 13 periods.",
            )
    
            # Ask if user wants to activate the new FY
            reply = QMessageBox.question(
                None,
                "Activate New FY",
                f"Do you want to activate {fy_string}?\n\n"
                "This will close all other open financial years (except the current active one) "
                "and set this as the active financial year.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
    
            if reply == QMessageBox.Yes:
                self.activate_fy(new_fy_id)
    
            # Refresh the list and highlight new FY
            self.load_financial_years()
    
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
    
            QMessageBox.critical(
                None, "Error", f"Failed to create financial year: {str(e)}"
            )

def create_next_fy(self) -> int:
    """
    Create the next sequential financial year automatically.
    
    Returns:
        int: The ID of the new financial year, or None on error.
    """
    try:
        from datetime import date
        
        next_fy_str = self.utils.get_fy_from_date(date(date.today().year + 1, 4, 1))
        fy_id = self.utils.get_or_create_fy(next_fy_str)
        
        # Log the action
        from scripts.Utilities.audit_utils import save_audit_log
        
        save_audit_log(
            "FY_CREATED_NEXT",
            f"Auto-created next financial year {next_fy_str}",
            fy_id,
        )
        
        return fy_id
        
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.critical(
            None, "Error", f"Failed to create next financial year: {str(e)}"
        )
        return None
def activate_fy(self, fy_id: int) -> None:
    """
    Activate a financial year: close other open FYs except current active, set target as active.
    
    Args:
        fy_id: The ID of the FY to activate.
    """
    try:
        # Get FY details for confirmation
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT start_year, end_year FROM financial_years WHERE id = ?",
            (fy_id,)
        )
        fy_result = cursor.fetchone()
        conn.close()
        if not fy_result:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Error", "Selected financial year not found.")
            return
        
        start_year, end_year = fy_result
        fy_string = f"{start_year}-{end_year}"
        
        # Confirm activation
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None,
            "Confirm Activation",
            f"Are you sure you want to activate {fy_string}?\n\n"
            "This will close all other open financial years (except the current active one) "
            "and set {fy_string} as the active financial year.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.utils.activate_fy(fy_id)
        
        # Log the action
        from scripts.Utilities.audit_utils import save_audit_log
        
        save_audit_log(
            "FY_ACTIVATED",
            f"Financial year {fy_string} activated",
            fy_id,
        )
        
        QMessageBox.information(
            None,
            "Success",
            f"Financial year {fy_string} activated successfully.",
        )
        
        self.load_financial_years()
        
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.critical(
            None, "Error", f"Failed to activate financial year: {str(e)}"
        )

    def open_financial_year(self) -> None:
        """
        Open a financial year for transactions.
        """
        current_item = self.dialog.fy_tree.currentItem()
        if not current_item:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None, "No Selection", "Please select a financial year to open."
            )
            return

        if current_item.is_open:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                None, "Already Open", "This financial year is already open."
            )
            return

        # Confirm opening
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            None,
            "Confirm Open",
            f"Are you sure you want to open financial year {current_item.fy_string}?\n\n"
            "This will allow transactions to be recorded for this financial year.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success, message = self._update_fy_status(current_item.fy_id, True)
            if success:
                QMessageBox.information(
                    None,
                    "Success",
                    f"Financial year {current_item.fy_string} opened successfully.",
                )
                self.load_financial_years()
            else:
                QMessageBox.warning(
                    None, "Error", f"Failed to open financial year: {message}"
                )

    def close_financial_year(self) -> None:
        """
        Close a financial year.
        """
        current_item = self.dialog.fy_tree.currentItem()
        if not current_item:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None, "No Selection", "Please select a financial year to close."
            )
            return

        if not current_item.is_open:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                None, "Already Closed", "This financial year is already closed."
            )
            return

        # Validate closure
        try:
            validation = self.utils.validate_fy_closure(current_item.fy_id)
            if not validation['can_close']:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    None,
                    "Cannot Close",
                    "Cannot close financial year: " + "; ".join(validation['issues']),
                )
                return
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None,
                "Validation Error",
                f"Failed to validate closure: {str(e)}",
            )
            return

        # Confirm closing
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            None,
            "Confirm Close",
            f"Are you sure you want to close financial year {current_item.fy_string}?\n\n"
            "This will prevent any further transactions for this financial year.\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                self.utils.close_fy(current_item.fy_id)
                
                # Log the action
                from scripts.Utilities.audit_utils import save_audit_log
                save_audit_log(
                    "FY_CLOSED",
                    f"Closed financial year {current_item.fy_string}",
                    current_item.fy_id,
                )

                QMessageBox.information(
                    None,
                    "Success",
                    f"Financial year {current_item.fy_string} closed successfully.",
                )
                self.load_financial_years()
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    None, "Error", f"Failed to close financial year: {str(e)}"
                )

    def _validate_fy_format(self, fy_string: str) -> bool:
        """Validate financial year string format."""
        import re

        return bool(re.match(r"^\d{4}-\d{2}$", fy_string))

    def _update_fy_status(self, fy_id: int, is_open: bool) -> Tuple[bool, str]:
        """Update financial year status."""
        try:
            import sqlite3
            from datetime import datetime

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE financial_years
                SET status = ?
                WHERE id = ?
                """,
                ('open' if is_open else 'closed', fy_id),
            )

            conn.commit()
            conn.close()
            return True, "Status updated successfully"

        except Exception as e:
            return False, str(e)

    # _can_close_fy removed - delegated to CentralFYUtils.validate_fy_closure
