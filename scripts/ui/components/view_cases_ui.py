import os
from datetime import datetime
from functools import partial

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (QComboBox, QDialog, QFormLayout, QGroupBox,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea, QSplitter,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                             QWidget)
from scripts.case_management_modules.case_table_utils import \
    setup_case_table_columns
from scripts.case_management_modules.view_cases_logic import ViewCasesLogic
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (get_all_financial_years,
                                               get_current_open_financial_year,
                                               get_financial_year)
from scripts.Utilities.responsibility_utils import load_responsibilities
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.ui_theme import apply_theme, create_professional_button
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.view_cases_utils import ViewCasesUtils


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


class ViewCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Cases")
        self.setFixedSize(
            1700, 600
        )  # Increased by another ~10% (160px) for optimal header visibility
        self.responsibilities = load_responsibilities()

        # Apply professional theme
        apply_theme(self)

        self.setup_ui()

    def populate_fy_filter(self):
        """Populate the financial year filter combo box"""
        self.fy_filter_combo.clear()

        # Get all financial years
        financial_years = get_all_financial_years()

        # Add financial years to combo box
        for fy_id, fy_string, is_open in financial_years:
            self.fy_filter_combo.addItem(fy_string, fy_id)

        # Set current open financial year as default
        current_open = get_current_open_financial_year()
        if current_open:
            fy_id, fy_string = current_open
            index = self.fy_filter_combo.findData(fy_id)
            if index >= 0:
                self.fy_filter_combo.setCurrentIndex(index)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Compact search bars layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(10)

        # Financial Year filter
        fy_label = QLabel("FY:")
        fy_label.setFixedWidth(20)
        self.fy_filter_combo = NoWheelComboBox()
        self.fy_filter_combo.setFixedWidth(120)
        self.populate_fy_filter()
        self.fy_filter_combo.currentTextChanged.connect(
            lambda: ViewCasesLogic.refresh_cases(self)
        )

        search_layout.addWidget(fy_label)
        search_layout.addWidget(self.fy_filter_combo)

        # Separator
        search_layout.addSpacing(20)

        # Responsibility search
        resp_label = QLabel("Responsibility:")
        resp_label.setFixedWidth(80)
        self.resp_search_edit = QLineEdit()
        self.resp_search_edit.setPlaceholderText("Type to search...")
        self.resp_search_edit.setFixedWidth(200)
        self.resp_search_edit.textChanged.connect(self.filter_responsibilities)

        search_layout.addWidget(resp_label)
        search_layout.addWidget(self.resp_search_edit)

        # Separator
        search_layout.addSpacing(20)

        # List filter - compact layout
        list_label = QLabel("List:")
        list_label.setFixedWidth(30)
        self.list_filter_combo = NoWheelComboBox()
        self.list_filter_combo.addItems(
            [
                "Checklist",
                "Lead Schedule",
                "To-Do List",
                "Recovered",
                "Write-Off Recommended",
                "Written Off",
                "Deleted Cases",
            ]
        )
        self.list_filter_combo.setCurrentText("Checklist")
        self.list_filter_combo.setFixedWidth(
            140
        )  # Increased width for longer list names
        self.list_filter_combo.currentTextChanged.connect(
            lambda: (
                ViewCasesLogic.refresh_cases(self),
                ViewCasesLogic.update_write_off_buttons_visibility(self),
            )
        )

        search_layout.addWidget(list_label)
        search_layout.addWidget(self.list_filter_combo)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Write-Off Recommended specific buttons (shown only when in that list)
        self.write_off_buttons_layout = QHBoxLayout()
        self.write_off_buttons_layout.setContentsMargins(5, 0, 5, 10)
        self.write_off_buttons_layout.setSpacing(10)

        self.create_submission_btn = create_professional_button(
            "Create Write-Off Submission", "primary"
        )
        self.create_submission_btn.clicked.connect(
            lambda: ViewCasesLogic.create_write_off_submission(self)
        )
        self.create_submission_btn.setVisible(False)  # Hidden by default
        self.write_off_buttons_layout.addWidget(self.create_submission_btn)

        self.approve_submission_btn = create_professional_button(
            "Approve Write-Off Submission", "success"
        )
        self.approve_submission_btn.clicked.connect(
            lambda: ViewCasesLogic.approve_write_off_submission(self)
        )
        self.approve_submission_btn.setVisible(False)  # Hidden by default
        self.write_off_buttons_layout.addWidget(self.approve_submission_btn)

        # Excel export button (available for all lists)
        self.excel_export_btn = create_professional_button("Export to Excel", "info")
        self.excel_export_btn.clicked.connect(
            lambda: ViewCasesUtils.export_to_excel(self)
        )
        self.write_off_buttons_layout.addWidget(self.excel_export_btn)

        self.write_off_buttons_layout.addStretch()
        layout.addLayout(self.write_off_buttons_layout)

        # Main content layout
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        setup_case_table_columns(self.case_table, include_edit=False)

        # Enable selection change to highlight responsibility
        self.case_table.itemSelectionChanged.connect(self.on_case_select)
        # Enable double-click to view case details
        self.case_table.itemDoubleClicked.connect(
            lambda item: ViewCasesLogic.show_case_details(
                self, item, self.list_filter_combo.currentText()
            )
        )

        # Set minimum width for headers and enable proper resizing
        header = self.case_table.horizontalHeader()
        header.setMinimumSectionSize(80)  # Minimum width for each column
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        header.setStretchLastSection(
            True
        )  # Last column stretches to fill remaining space

        # Set row height for better readability
        self.case_table.verticalHeader().setDefaultSectionSize(25)

        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)
        ViewCasesLogic.refresh_responsibilities(self)
        ViewCasesLogic.refresh_cases(self)

    def on_resp_select(self):
        ViewCasesLogic.on_resp_select(self)

    def on_case_select(self):
        ViewCasesLogic.on_case_select(self)

    def filter_responsibilities(self, text):
        ViewCasesLogic.filter_responsibilities(self, text)


class CaseDetailsDialog(QDialog):
    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.case_data = case_data
        self.setWindowTitle(
            f"Case Details - {case_data[1]}"
        )  # case_data[1] is transaction_no
        self.setFixedSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create scroll area for case details
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)

        # Case Information Section
        case_info_group = QGroupBox("Case Information")
        case_info_layout = QFormLayout(case_info_group)

        case_info_layout.addRow("Case No:", QLabel(self.case_data[1]))
        case_info_layout.addRow(
            "Date Incurred:", QLabel(self.case_data[2] if self.case_data[2] else "N/A")
        )
        case_info_layout.addRow(
            "Date Identified:",
            QLabel(self.case_data[3] if self.case_data[3] else "N/A"),
        )
        case_info_layout.addRow(
            "Date Reported:", QLabel(self.case_data[4] if self.case_data[4] else "N/A")
        )
        case_info_layout.addRow(
            "Category:", QLabel(self.case_data[9] if self.case_data[9] else "N/A")
        )
        case_info_layout.addRow(
            "Amount:",
            QLabel(
                format_currency_amount(self.case_data[11])
                if self.case_data[11]
                else "N/A"
            ),
        )
        case_info_layout.addRow(
            "List:", QLabel(self.case_data[16] if self.case_data[16] else "N/A")
        )
        case_info_layout.addRow(
            "Status:", QLabel(self.case_data[15] if self.case_data[15] else "N/A")
        )

        scroll_layout.addRow(case_info_group)

        # Description Section
        if self.case_data[5]:  # description
            desc_group = QGroupBox("Description")
            desc_layout = QVBoxLayout(desc_group)
            desc_text = QTextEdit()
            desc_text.setPlainText(self.case_data[5])
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            desc_layout.addWidget(desc_text)
            scroll_layout.addRow(desc_group)

        # Financial Information Section
        financial_group = QGroupBox("Financial Information")
        financial_layout = QFormLayout(financial_group)

        financial_layout.addRow(
            "BAS Payment No:", QLabel(self.case_data[6] if self.case_data[6] else "N/A")
        )
        financial_layout.addRow(
            "BAS Payment Date:",
            QLabel(self.case_data[7] if self.case_data[7] else "N/A"),
        )
        financial_layout.addRow(
            "BAS Journal No:",
            QLabel(
                self.case_data[29]
                if len(self.case_data) > 29 and self.case_data[29]
                else "N/A"
            ),
        )
        financial_layout.addRow(
            "BAS Journal Date:",
            QLabel(
                self.case_data[30]
                if len(self.case_data) > 30 and self.case_data[30]
                else "N/A"
            ),
        )
        financial_layout.addRow(
            "Persal No:", QLabel(self.case_data[8] if self.case_data[8] else "N/A")
        )

        scroll_layout.addRow(financial_group)

        # Assessment Information Section
        if (
            self.case_data[18] or self.case_data[19]
        ):  # assessment_assessed_by or assessment_date
            assessment_group = QGroupBox("Assessment Information")
            assessment_layout = QFormLayout(assessment_group)

            assessment_layout.addRow(
                "Assessed By:",
                QLabel(self.case_data[18] if self.case_data[18] else "N/A"),
            )
            assessment_layout.addRow(
                "Assessment Date:",
                QLabel(self.case_data[19] if self.case_data[19] else "N/A"),
            )

            scroll_layout.addRow(assessment_group)

        # Additional Information Section
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)

        additional_layout.addRow(
            "Criminal Charges:",
            QLabel(
                self.case_data[22]
                if len(self.case_data) > 22 and self.case_data[22]
                else "N/A"
            ),
        )
        additional_layout.addRow(
            "Disciplinary Process:",
            QLabel(
                self.case_data[23]
                if len(self.case_data) > 23 and self.case_data[23]
                else "N/A"
            ),
        )
        additional_layout.addRow(
            "Loss Recovery:",
            QLabel(
                self.case_data[24]
                if len(self.case_data) > 24 and self.case_data[24]
                else "N/A"
            ),
        )

        scroll_layout.addRow(additional_group)

        # Prevention Steps Section
        if len(self.case_data) > 25 and self.case_data[25]:  # prevention_steps
            prevention_group = QGroupBox("Prevention Steps")
            prevention_layout = QVBoxLayout(prevention_group)
            prevention_text = QTextEdit()
            prevention_text.setPlainText(self.case_data[25])
            prevention_text.setReadOnly(True)
            prevention_text.setMaximumHeight(100)
            prevention_layout.addWidget(prevention_text)
            scroll_layout.addRow(prevention_group)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Close button
        button_layout = QHBoxLayout()
        close_button = create_professional_button("Close", "secondary")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
