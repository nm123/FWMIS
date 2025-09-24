"""
Basic UI setup for EditCaseDialog.
Handles basic case information components.
"""

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QDateEdit, QFormLayout, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QWidget)
from scripts.ui.components.custom_widgets import NoWheelComboBox
from scripts.Utilities.workflow_utils import get_display_transaction_no


def setup_basic_ui_components(dialog_instance):
    """
    Set up basic case information UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== BASIC CASE INFORMATION GROUP =====
    basic_group = QGroupBox("Basic Case Information")
    basic_layout = QFormLayout(basic_group)

    # Case Number and Amount in one row
    case_amount_layout = QHBoxLayout()
    
    # Case Number (read-only) - show base number + current suffixes
    display_transaction_no = get_display_transaction_no(
        dialog_instance.base_transaction_no, dialog_instance.suffixes
    )
    dialog_instance.trans_no_edit = QLineEdit(display_transaction_no)
    dialog_instance.trans_no_edit.setReadOnly(True)
    case_amount_layout.addWidget(dialog_instance.trans_no_edit)
    
    # Amount
    dialog_instance.amount_edit = QLineEdit()
    case_amount_layout.addWidget(QLabel("Amount:"))
    case_amount_layout.addWidget(dialog_instance.amount_edit)
    
    basic_layout.addRow("Case No:", case_amount_layout)

    # Responsibility and Category in one row
    resp_category_layout = QHBoxLayout()
    
    # Responsibility
    resp_layout = QHBoxLayout()
    dialog_instance.responsibility_edit = QLineEdit()
    dialog_instance.responsibility_edit.setReadOnly(True)
    dialog_instance.responsibility_edit.setPlaceholderText(
        "Click Select to choose responsibility..."
    )
    resp_layout.addWidget(dialog_instance.responsibility_edit)

    dialog_instance.select_responsibility_button = QPushButton("Select")
    dialog_instance.select_responsibility_button.clicked.connect(
        dialog_instance.select_responsibility
    )
    resp_layout.addWidget(dialog_instance.select_responsibility_button)
    
    resp_category_layout.addLayout(resp_layout)

    # Category
    dialog_instance.category_combo = NoWheelComboBox()
    dialog_instance.category_combo.addItems(
        [c["name"] for c in dialog_instance.categories]
    )
    # Connect category change to update conditional fields
    dialog_instance.category_combo.currentTextChanged.connect(
        lambda: dialog_instance.update_conditional_fields()
    )
    resp_category_layout.addWidget(QLabel("Category:"))
    resp_category_layout.addWidget(dialog_instance.category_combo)
    
    basic_layout.addRow("Responsibility:", resp_category_layout)

    # Date fields (improved grid layout for better alignment)
    date_group = QWidget()
    date_layout = QGridLayout(date_group)
    date_layout.setContentsMargins(0, 0, 0, 0)
    date_layout.setSpacing(10)

    # Date Incurred
    date_incurred_label = QLabel("Date Incurred:")
    date_incurred_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_incurred_label, 0, 0)
    dialog_instance.date_incurred_edit = QDateEdit(QDate.currentDate())
    dialog_instance.date_incurred_edit.setCalendarPopup(True)
    dialog_instance.date_incurred_edit.setFixedWidth(120)
    date_layout.addWidget(dialog_instance.date_incurred_edit, 0, 1)

    # Date Identified
    date_identified_label = QLabel("Date Identified:")
    date_identified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_identified_label, 0, 2)
    dialog_instance.date_identified_edit = QDateEdit(QDate.currentDate())
    dialog_instance.date_identified_edit.setCalendarPopup(True)
    dialog_instance.date_identified_edit.setFixedWidth(120)
    date_layout.addWidget(dialog_instance.date_identified_edit, 0, 3)

    # Date Reported
    date_reported_label = QLabel("Date Reported:")
    date_reported_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_reported_label, 0, 4)
    dialog_instance.date_reported_edit = QDateEdit(QDate.currentDate())
    dialog_instance.date_reported_edit.setCalendarPopup(True)
    dialog_instance.date_reported_edit.setFixedWidth(120)
    date_layout.addWidget(dialog_instance.date_reported_edit, 0, 5)

    basic_layout.addRow("Dates:", date_group)

    # Description (reduced height for better space efficiency)
    dialog_instance.description_edit = QTextEdit()
    dialog_instance.description_edit.setMinimumHeight(40)
    dialog_instance.description_edit.setMaximumHeight(40)  # Force height to prevent overrides
    basic_layout.addRow("Description:", dialog_instance.description_edit)

    dialog_instance.main_layout.addWidget(basic_group)


# End of File
