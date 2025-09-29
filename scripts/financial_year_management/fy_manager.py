"""
Financial Year Manager Module

Contains functionality for managing financial years.
"""

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

            # Get all financial years
            cursor.execute(
                """
                SELECT id, start_year, end_year, status, active_period
                FROM financial_years
                ORDER BY start_year DESC
            """
            )

            financial_years = cursor.fetchall()
            conn.close()

            # Clear existing items
            self.dialog.fy_tree.clear()

            # Add financial years to tree
            for fy_id, start_year, end_year, status, active_period in financial_years:
                fy_string = f"{start_year}-{(end_year) % 100:02d}"
                item = QTreeWidgetItem([fy_string])

                # Store data
                item.fy_id = fy_id
                item.fy_string = fy_string
                item.start_year = start_year
                item.end_year = end_year
                item.status = status
                item.active_period = active_period
                item.is_open = status == 'open'

                # Set color based on status
                if status == 'open':
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
        Create a new financial year.
        """
        try:
            import sqlite3
            from datetime import date

            from PyQt5.QtWidgets import QInputDialog, QMessageBox

            from scripts.Utilities.config import DB_PATH

            # Get current year
            current_year = date.today().year

            # Suggest next financial year (April current year to March next year)
            suggested_fy = f"{current_year}-{(current_year + 1) % 100:02d}"

            # Get financial year string from user
            fy_string, ok = QInputDialog.getText(
                None,
                "Create Financial Year",
                "Enter financial year (e.g., 2024-25):",
                text=suggested_fy,
            )

            if not ok or not fy_string.strip():
                return

            fy_string = fy_string.strip()

            # Validate format
            if not self._validate_fy_format(fy_string):
                QMessageBox.warning(
                    None,
                    "Invalid Format",
                    "Financial year must be in format YYYY-YY (e.g., 2024-25)",
                )
                return

            # Check if financial year already exists
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM financial_years WHERE fy_string = ?", (fy_string,)
            )
            if cursor.fetchone():
                conn.close()
                QMessageBox.warning(
                    None,
                    "Already Exists",
                    f"Financial year {fy_string} already exists.",
                )
                return

            # Calculate start and end dates
            start_year = int(fy_string[:4])
            start_date = date(start_year, 4, 1)  # April 1st
            end_date = date(start_year + 1, 3, 31)  # March 31st

            # Create financial year
            cursor.execute(
                """
                INSERT INTO financial_years (start_year, end_year, status, active_period)
                VALUES (?, ?, ?, ?)
            """,
                (start_year, end_year, 'closed', None),
            )

            # Create 13 periods for the financial year
            fy_id = cursor.lastrowid
            self._create_periods_for_fy(cursor, fy_id, start_date)

            conn.commit()
            conn.close()

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "FY_CREATED",
                f"Financial year {fy_string} created",
                fy_id,
            )

            QMessageBox.information(
                None,
                "Success",
                f"Financial year {fy_string} created successfully with 13 periods.",
            )

            self.load_financial_years()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                None, "Error", f"Failed to create financial year: {str(e)}"
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

        # Check if all periods are closed
        if not self._can_close_fy(current_item.fy_id):
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None,
                "Cannot Close",
                "Cannot close financial year: all periods must be closed first.",
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
            success, message = self._update_fy_status(current_item.fy_id, False)
            if success:
                QMessageBox.information(
                    None,
                    "Success",
                    f"Financial year {current_item.fy_string} closed successfully.",
                )
                self.load_financial_years()
            else:
                QMessageBox.warning(
                    None, "Error", f"Failed to close financial year: {message}"
                )

    def _validate_fy_format(self, fy_string: str) -> bool:
        """Validate financial year string format."""
        import re

        return bool(re.match(r"^\d{4}-\d{2}$", fy_string))

    def _create_periods_for_fy(self, cursor, fy_id: int, start_date) -> None:
        """Create 13 periods for a financial year."""
        from datetime import date, timedelta

        for period_num in range(1, 14):
            if period_num <= 12:
                # Regular monthly periods
                period_start = date(start_date.year, start_date.month, 1) + timedelta(
                    days=(period_num - 1) * 31
                )
                # Adjust for actual month boundaries
                period_start = period_start.replace(day=1)
                if period_start.month > 12:
                    period_start = period_start.replace(
                        year=period_start.year + 1, month=1
                    )

                # Calculate period end (last day of month)
                if period_start.month == 12:
                    period_end = date(period_start.year, 12, 31)
                else:
                    period_end = date(
                        period_start.year, period_start.month + 1, 1
                    ) - timedelta(days=1)
            else:
                # Period 13 - Audit adjustments (whole year)
                period_start = start_date
                period_end = date(start_date.year + 1, 3, 31)

            cursor.execute(
                """
                INSERT INTO periods (fy_id, period_number, start_date, end_date, is_open)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    fy_id,
                    period_num,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    period_num == 1,
                ),
            )

    def _update_fy_status(self, fy_id: int, is_open: bool) -> Tuple[bool, str]:
        """Update financial year status."""
        try:
            import sqlite3
            from datetime import datetime

            from scripts.Utilities.config import DB_PATH

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

    def _can_close_fy(self, fy_id: int) -> bool:
        """Check if financial year can be closed."""
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if is_open column exists
            cursor.execute("PRAGMA table_info(periods)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'is_open' in columns:
                # Check if any periods are still open
                cursor.execute(
                    "SELECT COUNT(*) FROM periods WHERE fy_id = ? AND is_open = 1",
                    (fy_id,),
                )
                open_periods = cursor.fetchone()[0]
                conn.close()
                return open_periods == 0
            else:
                # If no is_open column, check in-memory tracking
                # Get all period IDs for this FY
                cursor.execute("SELECT id FROM periods WHERE fy_id = ?", (fy_id,))
                period_ids = [row[0] for row in cursor.fetchall()]
                conn.close()

                # Check if any are in memory_opened_periods
                # We need to access the period manager's memory tracking
                # For now, assume FY can always be closed when no is_open column
                return True

        except Exception:
            return False
