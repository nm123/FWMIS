import sqlite3
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QLabel, QFrame, QSplitter, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QColor
from scripts.Utilities.config import DB_PATH

# Color constants for consistent theming
COLOR_OPEN = QColor(144, 238, 144)      # Light green
COLOR_CLOSED = QColor(211, 211, 211)    # Light gray
COLOR_LOCKED = QColor(255, 0, 0)        # Red

class FinancialYearManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Financial Years & Periods")
        self.setFixedSize(900, 700)
        self.setup_ui()
        self.load_financial_years()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Financial Year & Period Management")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Info label
        info_label = QLabel(
            "Financial years run from 1 April to 31 March. Period 13 is for audit adjustments.\n"
            "A period can only be closed when all cases are finalized. Period 13 can only open after Period 12 closes."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(info_label)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Financial Years
        fy_group = QGroupBox("Financial Years")
        fy_layout = QVBoxLayout()

        self.fy_tree = QTreeWidget()
        self.fy_tree.setHeaderLabel("Financial Years")
        self.fy_tree.itemSelectionChanged.connect(self.on_fy_select)
        fy_layout.addWidget(self.fy_tree)

        # FY buttons
        fy_buttons_layout = QHBoxLayout()
        self.create_fy_button = QPushButton("Create New FY")
        self.create_fy_button.clicked.connect(self.create_financial_year)
        self.open_fy_button = QPushButton("Open FY")
        self.open_fy_button.clicked.connect(self.open_financial_year)
        self.close_fy_button = QPushButton("Close FY")
        self.close_fy_button.clicked.connect(self.close_financial_year)
        self.close_fy_button.setStyleSheet("QPushButton { color: red; }")

        fy_buttons_layout.addWidget(self.create_fy_button)
        fy_buttons_layout.addWidget(self.open_fy_button)
        fy_buttons_layout.addWidget(self.close_fy_button)
        fy_layout.addLayout(fy_buttons_layout)

        fy_group.setLayout(fy_layout)
        splitter.addWidget(fy_group)

        # Right panel - Periods
        periods_group = QGroupBox("Periods")
        periods_layout = QVBoxLayout()

        self.periods_tree = QTreeWidget()
        self.periods_tree.setHeaderLabels(["Period", "Status", "Start Date", "End Date", "Cases"])
        self.periods_tree.setColumnWidth(0, 80)
        self.periods_tree.setColumnWidth(1, 100)
        self.periods_tree.setColumnWidth(2, 100)
        self.periods_tree.setColumnWidth(3, 100)
        periods_layout.addWidget(self.periods_tree)

        # Period buttons
        period_buttons_layout = QHBoxLayout()
        self.open_period_button = QPushButton("Open Period")
        self.open_period_button.clicked.connect(self.open_period)
        self.close_period_button = QPushButton("Close Period")
        self.close_period_button.clicked.connect(self.close_period)
        self.close_period_button.setStyleSheet("QPushButton { color: red; }")

        period_buttons_layout.addWidget(self.open_period_button)
        period_buttons_layout.addWidget(self.close_period_button)
        periods_layout.addLayout(period_buttons_layout)

        periods_group.setLayout(periods_layout)
        splitter.addWidget(periods_group)

        splitter.setSizes([400, 500])
        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def load_financial_years(self):
        """Load all financial years into the tree"""
        self.fy_tree.clear()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, start_year, end_year, status, active_period
                FROM financial_years
                ORDER BY start_year DESC
            """)

            for fy in cursor.fetchall():
                fy_id, start_year, end_year, status, active_period = fy

                # Create tree item
                item_text = f"FY {start_year}-{end_year} ({status})"
                if active_period:
                    item_text += f" - Active: P{active_period}"

                item = QTreeWidgetItem([item_text])
                item.setData(0, Qt.UserRole, fy_id)

                # Color coding based on status
                if status == "open":
                    item.setBackground(0, COLOR_OPEN)
                elif status == "closed":
                    item.setBackground(0, COLOR_CLOSED)
                elif status == "locked":
                    item.setBackground(0, COLOR_LOCKED)

                self.fy_tree.addTopLevelItem(item)

            conn.close()

            if self.fy_tree.topLevelItemCount() > 0:
                self.fy_tree.setCurrentItem(self.fy_tree.topLevelItem(0))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load financial years: {e}")

    def on_fy_select(self):
        """Load periods for selected financial year"""
        selected = self.fy_tree.selectedItems()
        if not selected:
            return

        fy_id = selected[0].data(0, Qt.UserRole)
        self.load_periods(fy_id)

    def load_periods(self, fy_id):
        """Load periods for a specific financial year"""
        self.periods_tree.clear()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get financial year info
            cursor.execute("SELECT start_year, status FROM financial_years WHERE id = ?", (fy_id,))
            fy_info = cursor.fetchone()
            if not fy_info:
                return

            fy_start_year, fy_status = fy_info

            # Get all periods for this FY
            cursor.execute("""
                SELECT id, period_number, status, start_date, end_date
                FROM periods
                WHERE fy_id = ?
                ORDER BY period_number
            """, (fy_id,))

            periods = cursor.fetchall()

            # Count cases per period
            cursor.execute("""
                SELECT period_id, COUNT(*) as case_count
                FROM cases
                WHERE fy_id = ?
                GROUP BY period_id
            """, (fy_id,))

            case_counts = {row[0]: row[1] for row in cursor.fetchall()}

            for period in periods:
                period_id, period_number, status, start_date, end_date = period
                case_count = case_counts.get(period_id, 0)

                item = QTreeWidgetItem([
                    f"Period {period_number}",
                    status.title(),
                    start_date or "N/A",
                    end_date or "N/A",
                    str(case_count)
                ])

                item.setData(0, Qt.UserRole, period_id)
                item.setData(1, Qt.UserRole, period_number)

                # Color coding
                if status == "open":
                    item.setBackground(0, COLOR_OPEN)
                    item.setBackground(1, COLOR_OPEN)
                elif status == "closed":
                    item.setBackground(0, COLOR_CLOSED)
                    item.setBackground(1, COLOR_CLOSED)

                self.periods_tree.addTopLevelItem(item)

            conn.close()

            # Update status
            self.update_status(fy_id, fy_status)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load periods: {e}")

    def update_status(self, fy_id, fy_status):
        """Update the status label with current FY information"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Count open/closed periods
            cursor.execute("""
                SELECT status, COUNT(*) FROM periods
                WHERE fy_id = ? GROUP BY status
            """, (fy_id,))

            status_counts = dict(cursor.fetchall())
            open_count = status_counts.get('open', 0)
            closed_count = status_counts.get('closed', 0)

            conn.close()

            status_text = f"FY Status: {fy_status.title()} | Open Periods: {open_count} | Closed Periods: {closed_count}"
            self.status_label.setText(status_text)

        except sqlite3.Error as e:
            self.status_label.setText(f"Error loading status: {e}")

    def create_financial_year(self):
        """Create a new financial year"""
        # This would typically open a dialog to specify the year
        # For now, let's create FY 2026-2027 as an example
        reply = QMessageBox.question(
            self, "Create Financial Year",
            "Create Financial Year 2026-2027?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Check if FY already exists
                cursor.execute("SELECT id FROM financial_years WHERE start_year = 2026")
                if cursor.fetchone():
                    QMessageBox.warning(self, "Error", "Financial Year 2026-2027 already exists!")
                    conn.close()
                    return

                # Create new FY
                cursor.execute("""
                    INSERT INTO financial_years (start_year, end_year, status, active_period)
                    VALUES (2026, 2027, 'open', 1)
                """)

                fy_id = cursor.lastrowid

                # Create periods 1-12 with correct financial year dates
                months = [
                    (4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30),
                    (10, 31), (11, 30), (12, 31), (1, 31), (2, 28), (3, 31)
                ]

                for period_num in range(1, 13):
                    month_idx = period_num - 1
                    month, days = months[month_idx]

                    if period_num <= 9:  # April to December of start_year
                        year = 2026
                    else:  # January to March of end_year
                        year = 2027

                    start_date = f"{year}-{month:02d}-01"
                    end_date = f"{year}-{month:02d}-{days:02d}"

                    cursor.execute("""
                        INSERT INTO periods (fy_id, period_number, status, start_date, end_date)
                        VALUES (?, ?, 'closed', ?, ?)
                    """, (fy_id, period_num, start_date, end_date))

                # Open period 1
                cursor.execute("""
                    UPDATE periods SET status = 'open'
                    WHERE fy_id = ? AND period_number = 1
                """, (fy_id,))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", "Financial Year 2026-2027 created successfully!")
                self.load_financial_years()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to create financial year: {e}")

    def open_financial_year(self):
        """Open a closed financial year"""
        selected = self.fy_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a financial year to open.")
            return

        fy_id = selected[0].data(0, Qt.UserRole)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check current status
            cursor.execute("SELECT status FROM financial_years WHERE id = ?", (fy_id,))
            current_status = cursor.fetchone()[0]

            if current_status == "open":
                QMessageBox.information(self, "Already Open", "This financial year is already open.")
                conn.close()
                return

            # Open the FY
            cursor.execute("UPDATE financial_years SET status = 'open' WHERE id = ?", (fy_id,))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Financial year opened successfully!")
            self.load_financial_years()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to open financial year: {e}")

    def close_financial_year(self):
        """Close an open financial year"""
        selected = self.fy_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a financial year to close.")
            return

        fy_id = selected[0].data(0, Qt.UserRole)

        # Confirm closure
        reply = QMessageBox.question(
            self, "Confirm Close",
            "Are you sure you want to close this financial year?\n"
            "This will close all open periods in this financial year.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Close all open periods in this FY
                cursor.execute("""
                    UPDATE periods SET status = 'closed'
                    WHERE fy_id = ? AND status = 'open'
                """, (fy_id,))

                # Close the FY
                cursor.execute("UPDATE financial_years SET status = 'closed' WHERE id = ?", (fy_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", "Financial year closed successfully!")
                self.load_financial_years()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to close financial year: {e}")

    def open_period(self):
        """Open a closed period"""
        selected = self.periods_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a period to open.")
            return

        period_id = selected[0].data(0, Qt.UserRole)
        period_number = selected[0].data(1, Qt.UserRole)

        # Special handling for Period 13
        if period_number == 13:
            if not self.can_open_period_13():
                QMessageBox.warning(
                    self, "Cannot Open Period 13",
                    "Period 13 can only be opened after Period 12 is closed."
                )
                return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if period is already open
            cursor.execute("SELECT status FROM periods WHERE id = ?", (period_id,))
            current_status = cursor.fetchone()[0]

            if current_status == "open":
                QMessageBox.information(self, "Already Open", "This period is already open.")
                conn.close()
                return

            # Open the period
            cursor.execute("UPDATE periods SET status = 'open' WHERE id = ?", (period_id,))

            # Update FY active period to the highest open period
            cursor.execute("SELECT fy_id FROM periods WHERE id = ?", (period_id,))
            fy_id = cursor.fetchone()[0]

            # Find the highest open period for this FY
            cursor.execute("""
                SELECT MAX(period_number) FROM periods
                WHERE fy_id = ? AND status = 'open'
            """, (fy_id,))

            max_open_period = cursor.fetchone()[0]
            if max_open_period:
                cursor.execute("UPDATE financial_years SET active_period = ? WHERE id = ?", (max_open_period, fy_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", f"Period {period_number} opened successfully!")
            self.load_periods(fy_id)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to open period: {e}")

    def close_period(self):
        """Close an open period with validation"""
        selected = self.periods_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a period to close.")
            return

        period_id = selected[0].data(0, Qt.UserRole)
        period_number = selected[0].data(1, Qt.UserRole)

        # Special validation for Period 12
        if period_number == 12:
            validation_result = self.validate_period_12_closure(period_id)
            if not validation_result['can_close']:
                QMessageBox.warning(
                    self, "Cannot Close Period 12",
                    validation_result['message']
                )
                return

        # Check if there are any non-finalized cases
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE period_id = ? AND status NOT IN ('Confirmed', 'Valid')
            """, (period_id,))

            non_finalized_count = cursor.fetchone()[0]

            if non_finalized_count > 0:
                QMessageBox.warning(
                    self, "Cannot Close Period",
                    f"Cannot close Period {period_number}. There are {non_finalized_count} "
                    "cases that are not yet finalized (Confirmed or Valid)."
                )
                conn.close()
                return

            # Confirm closure
            reply = QMessageBox.question(
                self, "Confirm Close",
                f"Are you sure you want to close Period {period_number}?\n"
                "This action cannot be easily undone.",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Close the period
                cursor.execute("UPDATE periods SET status = 'closed' WHERE id = ?", (period_id,))

                # Get FY ID and update active period if needed
                cursor.execute("SELECT fy_id FROM periods WHERE id = ?", (period_id,))
                fy_id = cursor.fetchone()[0]

                # If this was the active period, update to the next highest open period
                cursor.execute("SELECT active_period FROM financial_years WHERE id = ?", (fy_id,))
                active_period = cursor.fetchone()[0]
                if active_period == period_number:
                    # Find the new highest open period
                    cursor.execute("""
                        SELECT MAX(period_number) FROM periods
                        WHERE fy_id = ? AND status = 'open'
                    """, (fy_id,))
                    new_active = cursor.fetchone()[0]
                    cursor.execute("UPDATE financial_years SET active_period = ? WHERE id = ?", (new_active, fy_id))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", f"Period {period_number} closed successfully!")
                self.load_periods(fy_id)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to close period: {e}")

    def validate_period_12_closure(self, period_id):
        """Validate if Period 12 can be closed by checking Checklist cases"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Count cases on Checklist with Alleged status
            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE period_id = ? AND list = 'Checklist' AND status = 'Alleged'
            """, (period_id,))
            alleged_count = cursor.fetchone()[0]

            # Count cases on Checklist with Under Assessment status
            cursor.execute("""
                SELECT COUNT(*) FROM cases
                WHERE period_id = ? AND list = 'Checklist' AND status = 'Under Assessment'
            """, (period_id,))
            under_assessment_count = cursor.fetchone()[0]

            conn.close()

            total_blocking_cases = alleged_count + under_assessment_count

            if total_blocking_cases > 0:
                message = f"Cannot close Period 12. There are {total_blocking_cases} cases on the Checklist that must be finalized:\n\n"
                message += f"• {alleged_count} cases with 'Alleged' status\n"
                message += f"• {under_assessment_count} cases with 'Under Assessment' status\n\n"
                message += "All cases for this financial year must be either 'Valid' or 'Confirmed' before Period 12 can be closed."

                return {
                    'can_close': False,
                    'message': message,
                    'alleged_count': alleged_count,
                    'under_assessment_count': under_assessment_count
                }
            else:
                return {'can_close': True}

        except sqlite3.Error as e:
            return {
                'can_close': False,
                'message': f"Database error while validating Period 12 closure: {e}"
            }

    def can_open_period_13(self):
        """Check if Period 13 can be opened (only after Period 12 is closed)"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get selected FY
            selected = self.fy_tree.selectedItems()
            if not selected:
                return False

            fy_id = selected[0].data(0, Qt.UserRole)

            # Check if Period 12 is closed
            cursor.execute("""
                SELECT status FROM periods
                WHERE fy_id = ? AND period_number = 12
            """, (fy_id,))

            period_12 = cursor.fetchone()
            conn.close()

            return period_12 and period_12[0] == 'closed'

        except sqlite3.Error:
            return False