"""
Basic UI setup for EditCaseDialog.
Handles basic case information components.
"""
from PyQt5.QtWidgets import QGroupBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QDateEdit, QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import QDate, Qt
from scripts.Utilities.workflow_utils import get_display_transaction_no
from scripts.ui.components.custom_widgets import NoWheelComboBox

def setup_basic_ui_components(dialog_instance):
    """
    Set up basic case information UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== BASIC CASE INFORMATION GROUP =====
    basic_group = QGroupBox("Basic Case Information")
    basic_layout = QFormLayout(basic_group)

    # Case Number (read-only) - show base number + current suffixes
    display_transaction_no = get_display_transaction_no(dialog_instance.base_transaction_no, dialog_instance.suffixes)
    dialog_instance.trans_no_edit = QLineEdit(display_transaction_no)
    dialog_instance.trans_no_edit.setReadOnly(True)
    basic_layout.addRow("Case No:", dialog_instance.trans_no_edit)

    # Responsibility
    resp_layout = QHBoxLayout()
    dialog_instance.responsibility_edit = QLineEdit()
    dialog_instance.responsibility_edit.setReadOnly(True)
    dialog_instance.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
    resp_layout.addWidget(dialog_instance.responsibility_edit)

    dialog_instance.select_responsibility_button = QPushButton("Select")
    dialog_instance.select_responsibility_button.clicked.connect(dialog_instance.select_responsibility)
    resp_layout.addWidget(dialog_instance.select_responsibility_button)

    basic_layout.addRow("Responsibility:", resp_layout)

    # Amount (moved here as it's crucial information)
    dialog_instance.amount_edit = QLineEdit()
    basic_layout.addRow("Amount:", dialog_instance.amount_edit)

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

    # Description (larger for paragraphs)
    dialog_instance.description_edit = QTextEdit()
    dialog_instance.description_edit.setMinimumHeight(80)
    basic_layout.addRow("Description:", dialog_instance.description_edit)

    # Evidence
    dialog_instance.evidence_edit = QLineEdit()
    dialog_instance.evidence_edit.setPlaceholderText("Select Evidence File")
    basic_layout.addRow("Evidence:", dialog_instance.evidence_edit)

    # Category and List
    category_list_layout = QHBoxLayout()
    dialog_instance.category_combo = NoWheelComboBox()
    dialog_instance.category_combo.addItems([c["name"] for c in dialog_instance.categories])
    category_list_layout.addWidget(QLabel("Category:"))
    category_list_layout.addWidget(dialog_instance.category_combo)

    category_list_layout.addSpacing(20)

    dialog_instance.list_combo = NoWheelComboBox()
    system_lists = [l["name"] for l in dialog_instance.lists if l.get("is_system", False)]
    dialog_instance.list_combo.addItems(system_lists)
    # Select default list
    if system_lists:
        default_list = next((l for l in dialog_instance.lists if l.get("is_default", False)), None)
        if default_list and default_list["name"] in system_lists:
            dialog_instance.list_combo.setCurrentText(default_list["name"])
    # Make list combo read-only since lists are managed by workflow
    dialog_instance.list_combo.setEnabled(False)
    category_list_layout.addWidget(QLabel("List:"))
    category_list_layout.addWidget(dialog_instance.list_combo)

    # Add visual indicator for list context
    current_list = dialog_instance.list_combo.currentText()
    if current_list == "Lead Schedule":
        context_label = QLabel("Appears in Loss Control Committee Review")
        context_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 12px;")
        category_list_layout.addSpacing(20)
        category_list_layout.addWidget(context_label)
    elif current_list == "Write-Off Recommended":
        context_label = QLabel("Write-Off Approval Pending")
        context_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 12px;")
        category_list_layout.addSpacing(20)
        category_list_layout.addWidget(context_label)

    basic_layout.addRow("", category_list_layout)

    # List and Status display
    dialog_instance.list_display_label = QLabel("List:")
    dialog_instance.list_display_value = QLabel(dialog_instance.selected_list or "Checklist")
    list_status_layout = QHBoxLayout()
    list_status_layout.addWidget(dialog_instance.list_display_label)
    list_status_layout.addWidget(dialog_instance.list_display_value)
    list_status_layout.addStretch()
    basic_layout.addRow("", list_status_layout)

    dialog_instance.status_display_label = QLabel("Status:")
    dialog_instance.status_display_value = QLabel()
    status_layout = QHBoxLayout()
    status_layout.addWidget(dialog_instance.status_display_label)
    status_layout.addWidget(dialog_instance.status_display_value)
    status_layout.addStretch()
    basic_layout.addRow("", status_layout)

    dialog_instance.main_layout.addWidget(basic_group)

# End of File