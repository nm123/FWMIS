"""
Period Manager Module

Contains functionality for managing financial periods.
"""

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from .dialog import FinancialYearManagementDialog


class PeriodManager:
    """
    Manages financial period operations.
    """

    def __init__(self, dialog: "FinancialYearManagementDialog"):
        """
        Initialize the period manager.

        Args:
            dialog: The parent FinancialYearManagementDialog instance
        """
        self.dialog = dialog

    def load_periods(self, fy_id: int) -> None:
        """
        Load periods for the selected financial year.

        Args:
            fy_id: Financial year ID
        """
        try:
            import sqlite3
            from datetime import datetime

            from PyQt5.QtGui import QColor
            from PyQt5.QtWidgets import QTreeWidgetItem

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get periods for financial year
            cursor.execute(
                """
                SELECT id, period_number, start_date, end_date, status
                FROM periods
                WHERE fy_id = ?
                ORDER BY period_number
            """,
                (fy_id,),
            )

            periods = cursor.fetchall()

            # If no periods exist for this financial year, create them
            if not periods:
                self._create_periods_for_fy(fy_id, cursor)
                conn.commit()
                # Re-fetch periods after creation
                cursor.execute(
                    """
                    SELECT id, period_number, start_date, end_date, status
                    FROM periods
                    WHERE fy_id = ?
                    ORDER BY period_number
                """,
                    (fy_id,),
                )
                periods = cursor.fetchall()

            # Get case counts for each period
            period_case_counts = {}
            for period in periods:
                period_id = period[0]
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE fy_id = ? AND date_reported >= ? AND date_reported <= ?
                """,
                    (fy_id, period[2], period[3]),
                )
                count = cursor.fetchone()[0]
                period_case_counts[period_id] = count

            conn.close()

            # Clear existing items
            self.dialog.periods_tree.clear()

            # Add periods to tree
            for period in periods:
                period_id, period_num, start_date, end_date, status = period

                # Format dates (handle None values)
                start_formatted = start_date if start_date else "N/A"
                end_formatted = end_date if end_date else "N/A"

                if start_formatted != "N/A":
                    try:
                        start_formatted = datetime.fromisoformat(str(start_date)).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        start_formatted = str(start_date)

                if end_formatted != "N/A":
                    try:
                        end_formatted = datetime.fromisoformat(str(end_date)).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        end_formatted = str(end_date)

                # Determine status based on period's status field
                is_effectively_open = status == "open"

                if period_num == 13 and not self.can_open_period_13(fy_id):
                    status = "Locked"
                    color = QColor(*self.dialog.ui_manager.COLOR_LOCKED)
                elif is_effectively_open:
                    status = "Open"
                    color = QColor(*self.dialog.ui_manager.COLOR_OPEN)
                else:
                    status = "Closed"
                    color = QColor(*self.dialog.ui_manager.COLOR_CLOSED)

                # Create tree item
                item = QTreeWidgetItem(
                    [
                        f"Period {period_num}",
                        status,
                        start_formatted,
                        end_formatted,
                        str(period_case_counts.get(period_id, 0)),
                    ]
                )

                item.setBackground(0, color)
                item.setBackground(1, color)
                item.setBackground(2, color)
                item.setBackground(3, color)
                item.setBackground(4, color)

                # Store data
                item.period_id = period_id
                item.period_number = period_num
                item.is_open = is_effectively_open

                self.dialog.periods_tree.addTopLevelItem(item)

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None, "Error", f"Failed to load periods: {str(e)}"
            )

    def open_period(self) -> None:
        """
        Open a financial period.
        """
        current_item = self.dialog.periods_tree.currentItem()
        if not current_item:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                None, "No Selection", "Please select a period to open."
            )
            return

        if current_item.is_open:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                None, "Already Open", "This period is already open."
            )
            return

        period_num = current_item.period_number

        # Special validation for period 13
        if period_num == 13:
            current_fy_item = self.dialog.fy_tree.currentItem()
            if current_fy_item and not self.can_open_period_13(current_fy_item.fy_id):
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.dialog,
                    "Cannot Open",
                    "Period 13 can only be opened after Period 12 is closed.",
                )
                return

        # Confirm opening
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self.dialog.dialog,
            "Confirm Open",
            f"Are you sure you want to open Period {period_num}?\n\n"
            "This will allow transactions to be recorded for this period.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success, message = self._update_period_status(current_item.period_id, True)
            if success:
                QMessageBox.information(
                    None, "Success", f"Period {period_num} opened successfully."
                )
                # Refresh periods display
                if self.dialog.fy_tree.currentItem():
                    current_fy_id = self.dialog.fy_tree.currentItem().fy_id
                    # Remember which period was selected
                    selected_period = None
                    if self.dialog.periods_tree.currentItem():
                        selected_period = self.dialog.periods_tree.currentItem().period_id

                    self.load_periods(current_fy_id)

                    # Restore the period selection
                    if selected_period is not None:
                        for i in range(self.dialog.periods_tree.topLevelItemCount()):
                            item = self.dialog.periods_tree.topLevelItem(i)
                            if hasattr(item, 'period_id') and item.period_id == selected_period:
                                self.dialog.periods_tree.setCurrentItem(item)
                                break
            else:
                QMessageBox.warning(
                    None, "Error", f"Failed to open period: {message}"
                )

    def close_period(self) -> None:
        """
        Close a financial period.
        """
        current_item = self.dialog.periods_tree.currentItem()
        if not current_item:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog.dialog, "No Selection", "Please select a period to close."
            )
            return

        if not current_item.is_open:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                self.dialog.dialog, "Already Closed", "This period is already closed."
            )
            return

        period_num = current_item.period_number

        # Check if period can be closed
        if not self._can_close_period(current_item.period_id):
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog.dialog,
                "Cannot Close",
                "Cannot close period: all cases in this period must be finalized first.",
            )
            return

        # Special validation for period 12 (must be closed before period 13 can open)
        if period_num == 12:
            if not self.validate_period_12_closure(current_item.period_id):
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.dialog.dialog,
                    "Validation Failed",
                    "Period 12 closure validation failed. Please ensure all requirements are met.",
                )
                return

        # Confirm closing
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self.dialog.dialog,
            "Confirm Close",
            f"Are you sure you want to close Period {period_num}?\n\n"
            "This will prevent any further transactions for this period.\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success, message = self._update_period_status(current_item.period_id, False)
            if success:
                QMessageBox.information(
                    None, "Success", f"Period {period_num} closed successfully."
                )
                # Refresh periods display
                if self.dialog.fy_tree.currentItem():
                    current_fy_id = self.dialog.fy_tree.currentItem().fy_id
                    # Remember which period was selected
                    selected_period = None
                    if self.dialog.periods_tree.currentItem():
                        selected_period = self.dialog.periods_tree.currentItem().period_id

                    self.load_periods(current_fy_id)

                    # Restore the period selection
                    if selected_period is not None:
                        for i in range(self.dialog.periods_tree.topLevelItemCount()):
                            item = self.dialog.periods_tree.topLevelItem(i)
                            if hasattr(item, 'period_id') and item.period_id == selected_period:
                                self.dialog.periods_tree.setCurrentItem(item)
                                break
            else:
                QMessageBox.warning(
                    None, "Error", f"Failed to close period: {message}"
                )

    def validate_period_12_closure(self, period_id: int) -> bool:
        """
        Validate period 12 closure requirements.

        Args:
            period_id: The period ID to validate

        Returns:
            bool: True if validation passes
        """
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get period details
            cursor.execute(
                """
                SELECT fy_id, period_number FROM periods WHERE id = ?
            """,
                (period_id,),
            )
            period_data = cursor.fetchone()

            if not period_data or period_data[1] != 12:
                conn.close()
                return False

            fy_id = period_data[0]

            # Check if all cases in the financial year are finalized
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE fy_id = ? AND status NOT IN ('Finalized', 'Write Off Recommended')
            """,
                (fy_id,),
            )

            unfinalized_cases = cursor.fetchone()[0]
            conn.close()

            return unfinalized_cases == 0

        except Exception as e:
            print(f"Error validating period 12 closure: {e}")
            return False

    def _create_periods_for_fy(self, fy_id: int, cursor) -> None:
        """
        Create 13 periods for a financial year if they don't exist.

        Args:
            fy_id: Financial year ID
            cursor: Database cursor
        """
        from datetime import date, timedelta

        # Get financial year start date
        cursor.execute("SELECT start_year FROM financial_years WHERE id = ?", (fy_id,))
        result = cursor.fetchone()
        if not result:
            return

        start_year = result[0]
        start_date = date(start_year, 4, 1)  # April 1st

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

            # Insert period with status column
            cursor.execute(
                """
                INSERT INTO periods (fy_id, period_number, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    fy_id,
                    period_num,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    "open" if period_num == 1 else "closed",  # Period 1 starts open
                ),
            )

    def can_open_period_13(self, fy_id: int) -> bool:
        """
        Check if period 13 can be opened for the given financial year.

        Args:
            fy_id: Financial year ID

        Returns:
            bool: True if period 13 can be opened
        """
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if is_open column exists
            cursor.execute("PRAGMA table_info(periods)")
            columns = [row[1] for row in cursor.fetchall()]

            # Check if period 12 is closed (status = 'closed')
            cursor.execute(
                "SELECT status FROM periods WHERE fy_id = ? AND period_number = 12",
                (fy_id,),
            )
            result = cursor.fetchone()
            conn.close()
            return result and result[0] == "closed"

        except Exception as e:
            print(f"Error checking period 13 availability: {e}")
            return False

    def _update_period_status(self, period_id: int, is_open: bool) -> Tuple[bool, str]:
        """Update period status by updating the period's status field."""
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Update the period's status directly in database
            cursor.execute(
                "UPDATE periods SET status = ? WHERE id = ?",
                ("open" if is_open else "closed", period_id),
            )
            conn.commit()
            conn.close()
            return True, "Status updated successfully"

        except Exception as e:
            return False, str(e)

    def _can_close_period(self, period_id: int) -> bool:
        """Check if period can be closed."""
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get period details
            cursor.execute(
                """
                SELECT fy_id, period_number, start_date, end_date FROM periods WHERE id = ?
            """,
                (period_id,),
            )
            period_data = cursor.fetchone()

            if not period_data:
                conn.close()
                return False

            fy_id, period_number, start_date, end_date = period_data

            # For periods 1-11: Allow closing regardless of unfinalized cases
            # (users may need to post transactions to previous periods)
            if period_number <= 11:
                conn.close()
                return True

            # For period 12: Special validation - cannot close if there are "Alleged" Checklist cases
            if period_number == 12:
                # Check for Alleged cases in Checklist (cases with status 'Alleged' that are in checklist)
                # Assuming checklist cases have list = 'Checklist' or similar identifier
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE fy_id = ? AND date_reported >= ? AND date_reported <= ?
                    AND assessment_status = 'Alleged'
                    AND list = 'Checklist'
                """,
                    (fy_id, start_date, end_date),
                )

                alleged_checklist_cases = cursor.fetchone()[0]
                conn.close()

                # Cannot close Period 12 if there are Alleged Checklist cases
                return alleged_checklist_cases == 0

            # For period 13: Allow closing (audit period)
            conn.close()
            return True

        except Exception as e:
            print(f"Error checking period closure: {e}")
            return False
