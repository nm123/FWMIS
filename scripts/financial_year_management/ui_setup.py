"""
UI Setup Module for Financial Year Management

Contains UI initialization and setup functionality for the financial year management dialog.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dialog import FinancialYearManagementDialog


class UISetupManager:
    """
    Manages UI setup and initialization for the financial year management dialog.
    """

    # Color constants for consistent theming
    COLOR_OPEN = (144, 238, 144)  # Light green
    COLOR_CLOSED = (211, 211, 211)  # Light gray
    COLOR_LOCKED = (255, 0, 0)  # Red

    def __init__(self, dialog: "FinancialYearManagementDialog"):
        """
        Initialize the UI setup manager.

        Args:
            dialog: The parent FinancialYearManagementDialog instance
        """
        self.dialog = dialog

    def setup_ui(self) -> None:
        """Set up the main dialog UI."""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import (
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QSplitter,
            QTreeWidget,
            QVBoxLayout,
        )

        layout = QVBoxLayout(self.dialog.dialog)
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
        info_label.setStyleSheet(
            "color: #666; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        layout.addWidget(info_label)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Financial Years
        fy_group = QGroupBox("Financial Years")
        fy_layout = QVBoxLayout()

        self.dialog.fy_tree = QTreeWidget()
        self.dialog.fy_tree.setHeaderLabel("Financial Years")
        self.dialog.fy_tree.itemSelectionChanged.connect(self.dialog.on_fy_select)
        fy_layout.addWidget(self.dialog.fy_tree)

        # FY buttons
        fy_buttons_layout = QHBoxLayout()
        self.dialog.create_fy_button = QPushButton("Create New FY")
        self.dialog.create_fy_button.clicked.connect(self.dialog.create_financial_year)
        self.dialog.open_fy_button = QPushButton("Open FY")
        self.dialog.open_fy_button.clicked.connect(self.dialog.open_financial_year)
        self.dialog.close_fy_button = QPushButton("Close FY")
        self.dialog.close_fy_button.clicked.connect(self.dialog.close_financial_year)
        self.dialog.close_fy_button.setStyleSheet("QPushButton { color: red; }")

        fy_buttons_layout.addWidget(self.dialog.create_fy_button)
        fy_buttons_layout.addWidget(self.dialog.open_fy_button)
        fy_buttons_layout.addWidget(self.dialog.close_fy_button)
        fy_layout.addLayout(fy_buttons_layout)

        fy_group.setLayout(fy_layout)
        splitter.addWidget(fy_group)

        # Right panel - Periods
        periods_group = QGroupBox("Periods")
        periods_layout = QVBoxLayout()

        self.dialog.periods_tree = QTreeWidget()
        self.dialog.periods_tree.setHeaderLabels(
            ["Period", "Status", "Start Date", "End Date", "Cases"]
        )
        self.dialog.periods_tree.setColumnWidth(0, 80)
        self.dialog.periods_tree.setColumnWidth(1, 100)
        self.dialog.periods_tree.setColumnWidth(2, 100)
        self.dialog.periods_tree.setColumnWidth(3, 100)
        periods_layout.addWidget(self.dialog.periods_tree)

        # Period buttons
        period_buttons_layout = QHBoxLayout()
        self.dialog.open_period_button = QPushButton("Open Period")
        self.dialog.open_period_button.clicked.connect(self.dialog.open_period)
        self.dialog.close_period_button = QPushButton("Close Period")
        self.dialog.close_period_button.clicked.connect(self.dialog.close_period)
        self.dialog.close_period_button.setStyleSheet("QPushButton { color: red; }")

        period_buttons_layout.addWidget(self.dialog.open_period_button)
        period_buttons_layout.addWidget(self.dialog.close_period_button)
        periods_layout.addLayout(period_buttons_layout)

        periods_group.setLayout(periods_layout)
        splitter.addWidget(periods_group)

        # Set splitter proportions
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)

        # Status label
        self.dialog.status_label = QLabel("")
        self.dialog.status_label.setStyleSheet(
            "color: blue; font-weight: bold; padding: 5px;"
        )
        layout.addWidget(self.dialog.status_label)
