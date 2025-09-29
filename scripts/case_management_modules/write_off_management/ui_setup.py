"""
UI Setup Module for Write-Off Management Dialog

Contains UI initialization and setup functionality for the write-off management dialog.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dialog import WriteOffManagementDialog


class UISetupManager:
    """
    Manages UI setup and initialization for the write-off management dialog.
    """

    def __init__(self, dialog: "WriteOffManagementDialog"):
        """
        Initialize the UI setup manager.

        Args:
            dialog: The parent WriteOffManagementDialog instance
        """
        self.dialog = dialog

    def setup_ui(self) -> None:
        """Set up the main dialog UI."""
        from PyQt5.QtWidgets import (
            QComboBox,
            QGroupBox,
            QHBoxLayout,
            QHeaderView,
            QLabel,
            QPushButton,
            QTableWidget,
            QVBoxLayout,
        )

        self.dialog.setWindowTitle("Write-Off Annexure Log")
        self.dialog.setFixedSize(1200, 800)

        layout = QVBoxLayout(self.dialog)

        # FY Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Financial Year:"))

        self.dialog.fy_filter_combo = QComboBox()
        self.dialog.fy_filter_combo.setFixedWidth(200)
        self.load_fy_filter()
        self.dialog.fy_filter_combo.currentTextChanged.connect(
            self.dialog.load_annexures
        )
        filter_layout.addWidget(self.dialog.fy_filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Annexures content directly in main layout
        annexures_group = QGroupBox("Write-Off Annexures")
        annexures_group_layout = QVBoxLayout(annexures_group)

        self.dialog.annexures_table = QTableWidget()
        self.dialog.annexures_table.setColumnCount(8)
        self.dialog.annexures_table.setHorizontalHeaderLabels(
            [
                "Annexure ID",
                "Created Date",
                "Status",
                "Cases",
                "Total Amount",
                "Actions",
                "Details",
                "Export",
            ]
        )

        # Set column widths
        header = self.dialog.annexures_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.dialog.annexures_table.setColumnWidth(0, 120)  # Annexure ID
        self.dialog.annexures_table.setColumnWidth(1, 120)  # Created Date
        self.dialog.annexures_table.setColumnWidth(2, 100)  # Status
        self.dialog.annexures_table.setColumnWidth(3, 80)  # Cases
        self.dialog.annexures_table.setColumnWidth(4, 120)  # Total Amount
        self.dialog.annexures_table.setColumnWidth(5, 200)  # Actions
        self.dialog.annexures_table.setColumnWidth(6, 150)  # Details
        self.dialog.annexures_table.setColumnWidth(7, 150)  # Export

        annexures_group_layout.addWidget(self.dialog.annexures_table)
        layout.addWidget(annexures_group)

        # Annexures action buttons
        annexures_btn_layout = QHBoxLayout()
        refresh_annexures_btn = QPushButton("Refresh Annexures")
        refresh_annexures_btn.clicked.connect(self.dialog.load_annexures)
        annexures_btn_layout.addWidget(refresh_annexures_btn)
        annexures_btn_layout.addStretch()
        layout.addLayout(annexures_btn_layout)

    def load_fy_filter(self) -> None:
        """
        Load financial years into the filter combo.
        """
        try:
            from scripts.Utilities.financial_utils import get_all_financial_years

            financial_years = get_all_financial_years()

            self.dialog.fy_filter_combo.clear()
            self.dialog.fy_filter_combo.addItem("All Years", None)

            for fy_id, fy_string, is_open in financial_years:
                display_text = f"{fy_string}"
                if is_open:
                    display_text += " (Open)"
                self.dialog.fy_filter_combo.addItem(display_text, fy_id)

            # Set current FY as default if available
            if hasattr(self.dialog, "fy") and self.dialog.fy:
                for i in range(self.dialog.fy_filter_combo.count()):
                    if self.dialog.fy_filter_combo.itemData(i) == self.dialog.fy:
                        self.dialog.fy_filter_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to load financial years: {str(e)}"
            )
            # Add a default option
            self.dialog.fy_filter_combo.addItem("Current Year", self.dialog.fy)
