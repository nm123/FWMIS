import os

from PyQt5.QtCore import QDate, QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (QComboBox, QDateEdit, QDialog, QFileDialog,
                             QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QScrollArea, QTextEdit, QVBoxLayout, QWidget)
from scripts.case_management_modules.responsibility_selection import \
    ResponsibilitySelectionDialog
from scripts.Utilities.ui_theme import apply_theme, create_professional_button


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


def setup_add_ui(dialog):
    """Set up the UI for AddNewCaseDialog"""
    # Apply professional theme
    apply_theme(dialog)

    # Initialize data with error handling
    try:
        from scripts.Utilities.category_utils import load_categories
        from scripts.Utilities.financial_utils import get_financial_year
        from scripts.Utilities.list_utils import load_lists
        from scripts.Utilities.responsibility_utils import \
            load_posting_responsibilities

        dialog.responsibilities = load_posting_responsibilities()
        dialog.categories = load_categories()
        dialog.lists = load_lists()
        dialog.fy = get_financial_year()
    except Exception as e:
        print(f"Warning: Error loading data: {e}")
        dialog.responsibilities = []
        dialog.categories = []
        dialog.lists = []
        dialog.fy = "2024"

    dialog.transaction_no = None
    dialog.selected_responsibility_id = None
    dialog.supporting_evidence_compulsory = False

    # Create main layout with reduced margins
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 10, 15, 15)
    layout.setSpacing(10)

    # Create scroll area for the form
    scroll_area = QScrollArea()
    scroll_widget = QWidget()
    main_layout = QVBoxLayout(scroll_widget)
    main_layout.setContentsMargins(5, 5, 5, 5)
    main_layout.setSpacing(8)

    # ===== BASIC CASE INFORMATION GROUP =====
    basic_group = QGroupBox("Basic Case Information")
    basic_layout = QFormLayout(basic_group)
    basic_layout.setContentsMargins(10, 15, 10, 10)
    basic_layout.setSpacing(8)
    basic_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Fix label alignment

    # Case Number
    dialog.trans_no_edit = QLineEdit("To be assigned")
    dialog.trans_no_edit.setReadOnly(True)
    basic_layout.addRow("Case No:", dialog.trans_no_edit)
    
    # Amount
    dialog.amount_edit = QLineEdit()
    basic_layout.addRow("Amount:", dialog.amount_edit)

    # Responsibility with Select button
    responsibility_layout = QHBoxLayout()
    dialog.responsibility_edit = QLineEdit()
    dialog.responsibility_edit.setReadOnly(True)
    dialog.responsibility_edit.setPlaceholderText(
        "Click Select to choose responsibility..."
    )
    responsibility_layout.addWidget(dialog.responsibility_edit)
    
    dialog.select_responsibility_button = create_professional_button(
        "Select", "info"  # Smaller button text
    )
    dialog.select_responsibility_button.setFixedWidth(80)  # Fixed smaller width
    dialog.select_responsibility_button.clicked.connect(dialog.select_responsibility)
    responsibility_layout.addWidget(dialog.select_responsibility_button)
    
    basic_layout.addRow("Responsibility:", responsibility_layout)

    # Category
    dialog.category_combo = NoWheelComboBox()
    if dialog.categories:
        dialog.category_combo.addItems([c["name"] for c in dialog.categories])
    basic_layout.addRow("Category:", dialog.category_combo)

    # Description (reduced height)
    dialog.description_edit = QTextEdit()
    dialog.description_edit.setMinimumHeight(40)
    dialog.description_edit.setMaximumHeight(40)
    basic_layout.addRow("Description:", dialog.description_edit)

    main_layout.addWidget(basic_group)

    # ===== DATE INFORMATION GROUP =====
    date_group = QGroupBox("Date Information")
    date_layout = QFormLayout(date_group)
    date_layout.setContentsMargins(10, 15, 10, 10)
    date_layout.setSpacing(8)
    date_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Fix label alignment

    # All dates in one horizontal row with labels to the left
    dates_layout = QHBoxLayout()
    
    # Date Incurred
    incurred_layout = QHBoxLayout()
    incurred_label = QLabel("Date Incurred:")
    incurred_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    incurred_layout.addWidget(incurred_label)
    dialog.date_incurred_edit = QDateEdit(QDate.currentDate())
    dialog.date_incurred_edit.setCalendarPopup(True)
    dialog.date_incurred_edit.setFixedWidth(150)
    incurred_layout.addWidget(dialog.date_incurred_edit)
    dates_layout.addLayout(incurred_layout)
    
    # Date Identified
    identified_layout = QHBoxLayout()
    identified_label = QLabel("Date Identified:")
    identified_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    identified_layout.addWidget(identified_label)
    dialog.date_identified_edit = QDateEdit(QDate.currentDate())
    dialog.date_identified_edit.setCalendarPopup(True)
    dialog.date_identified_edit.setFixedWidth(150)
    identified_layout.addWidget(dialog.date_identified_edit)
    dates_layout.addLayout(identified_layout)
    
    # Date Reported
    reported_layout = QHBoxLayout()
    reported_label = QLabel("Date Reported:")
    reported_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    reported_layout.addWidget(reported_label)
    dialog.date_reported_edit = QDateEdit(QDate.currentDate())
    dialog.date_reported_edit.setCalendarPopup(True)
    dialog.date_reported_edit.setFixedWidth(150)
    reported_layout.addWidget(dialog.date_reported_edit)
    dates_layout.addLayout(reported_layout)
    
    date_layout.addRow("", dates_layout)
    main_layout.addWidget(date_group)

    # ===== LIST AND STATUS INFORMATION GROUP =====
    status_evidence_group = QGroupBox("List and Status Information")
    status_evidence_layout = QFormLayout(status_evidence_group)
    status_evidence_layout.setContentsMargins(10, 15, 10, 10)
    status_evidence_layout.setSpacing(8)
    status_evidence_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Fix label alignment

    # Status field
    dialog.status_combo = NoWheelComboBox()
    dialog.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
    dialog.status_combo.setCurrentText("Alleged")
    dialog.status_combo.setFixedWidth(150)
    status_evidence_layout.addRow("Status:", dialog.status_combo)

    # List field
    dialog.list_combo = NoWheelComboBox()
    system_lists = [
        l["name"]
        for l in dialog.lists
        if l.get("is_system", False) and l["name"] != "Deleted Cases"
    ]
    dialog.list_combo.addItems(system_lists)
    # Always set to Checklist and disable selection
    if "Checklist" in system_lists:
        dialog.list_combo.setCurrentText("Checklist")
        dialog.list_combo.setEnabled(False)
    dialog.list_combo.setFixedWidth(150)
    status_evidence_layout.addRow("List:", dialog.list_combo)

    # Assessment Evidence with Browse button
    evidence_layout = QHBoxLayout()
    dialog.file_path_edit = QLineEdit()
    dialog.file_path_edit.setPlaceholderText("Select file...")
    evidence_layout.addWidget(dialog.file_path_edit)
    
    browse_button = create_professional_button("Browse", "info")  # Smaller button text
    browse_button.setFixedWidth(80)  # Fixed smaller width
    browse_button.clicked.connect(dialog.browse_file)
    evidence_layout.addWidget(browse_button)
    
    status_evidence_layout.addRow("Assessment Evidence:", evidence_layout)

    main_layout.addWidget(status_evidence_group)

    # ===== ADDITIONAL INFORMATION GROUP =====
    additional_group = QGroupBox("Additional Information")
    additional_main_layout = QVBoxLayout(additional_group)
    additional_main_layout.setContentsMargins(10, 15, 10, 10)
    additional_main_layout.setSpacing(8)

    # Split into two columns
    columns_layout = QHBoxLayout()
    
    # Left column - BAS Information
    bas_layout = QFormLayout()
    bas_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    bas_layout.setSpacing(8)
    
    # BAS Payment No
    dialog.bas_payment_no_edit = QLineEdit()
    bas_layout.addRow("BAS Payment No:", dialog.bas_payment_no_edit)
    
    # BAS Payment Date
    dialog.bas_payment_date_edit = QDateEdit(QDate.currentDate())
    dialog.bas_payment_date_edit.setCalendarPopup(True)
    dialog.bas_payment_date_edit.setFixedWidth(200)
    bas_layout.addRow("BAS Payment Date:", dialog.bas_payment_date_edit)

    # BAS Journal No
    dialog.bas_journal_no_edit = QLineEdit()
    bas_layout.addRow("BAS Journal No:", dialog.bas_journal_no_edit)
    
    # BAS Journal Date
    dialog.bas_journal_date_edit = QDateEdit(QDate.currentDate())
    dialog.bas_journal_date_edit.setCalendarPopup(True)
    dialog.bas_journal_date_edit.setFixedWidth(200)
    bas_layout.addRow("BAS Journal Date:", dialog.bas_journal_date_edit)
    
    columns_layout.addLayout(bas_layout)
    
    # Right column - Personnel Information
    personnel_layout = QFormLayout()
    personnel_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    personnel_layout.setSpacing(8)
    
    # Persal No field
    dialog.persal_no_edit = QLineEdit()
    personnel_layout.addRow("Persal No:", dialog.persal_no_edit)

    # Criminal Charges Laid
    dialog.criminal_charges_combo = NoWheelComboBox()
    dialog.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
    dialog.criminal_charges_combo.setCurrentText("N/A")
    personnel_layout.addRow("Criminal Charges Laid:", dialog.criminal_charges_combo)
    
    # Disciplinary Process
    dialog.disciplinary_combo = NoWheelComboBox()
    dialog.disciplinary_combo.addItems(["N/A", "Yes", "No"])
    dialog.disciplinary_combo.setCurrentText("N/A")
    personnel_layout.addRow("Disciplinary Process:", dialog.disciplinary_combo)
    
    columns_layout.addLayout(personnel_layout)
    
    additional_main_layout.addLayout(columns_layout)

    # Prevention steps (reduced height) - spans full width
    prevention_layout = QFormLayout()
    prevention_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    prevention_layout.setSpacing(8)
    
    dialog.prevention_steps_edit = QTextEdit()
    dialog.prevention_steps_edit.setMinimumHeight(40)
    dialog.prevention_steps_edit.setMaximumHeight(40)
    prevention_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog.prevention_steps_edit,
    )
    
    additional_main_layout.addLayout(prevention_layout)

    main_layout.addWidget(additional_group)


    # Set up scroll area
    scroll_area.setWidget(scroll_widget)
    scroll_area.setWidgetResizable(True)
    layout.addWidget(scroll_area)

    # Connect signals for real-time conditional field updates (will be called after method is defined)
    pass

    # Initialize conditional fields (safely)
    try:
        dialog.update_conditional_fields()
    except Exception as e:
        print(f"Warning: Could not initialize conditional fields: {e}")

    # Buttons
    button_layout = QHBoxLayout()
    button_layout.setContentsMargins(10, 10, 10, 10)
    dialog.save_button = create_professional_button("Save & Continue", "primary")
    dialog.save_button.clicked.connect(dialog.save_case)

    dialog.cancel_button = create_professional_button("Cancel", "secondary")
    dialog.cancel_button.clicked.connect(dialog.reject)

    button_layout.addWidget(dialog.save_button)
    button_layout.addWidget(dialog.cancel_button)
    layout.addLayout(button_layout)

    # Connect status change signal
    dialog.status_combo.currentTextChanged.connect(dialog.on_status_changed)

    # Connect category and list change signals for conditional field updates
    dialog.category_combo.currentTextChanged.connect(dialog.update_conditional_fields)
    dialog.list_combo.currentTextChanged.connect(dialog.update_conditional_fields)

    # Force form layout alignment after theme is applied
    def fix_form_alignment():
        """Fix form layout alignment after theme is applied"""
        try:
            # Find all form layouts and set their alignment
            for widget in dialog.findChildren(QFormLayout):
                widget.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        except Exception as e:
            print(f"Warning: Could not fix form alignment: {e}")

    # Apply alignment fix after a short delay to ensure theme is applied
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(100, fix_form_alignment)


class AssessmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Case Assessment")
        self.setFixedSize(400, 300)

        # Apply professional theme
        apply_theme(self)

        layout = QFormLayout(self)

        self.assessed_by_edit = QLineEdit()
        layout.addRow("Assessed By:", self.assessed_by_edit)

        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        layout.addRow("Assessment Date:", self.assessment_date_edit)

        self.result_combo = NoWheelComboBox()
        self.result_combo.addItems(["Valid", "Confirmed"])
        layout.addRow("Result:", self.result_combo)

        button_layout = QHBoxLayout()
        save_button = create_professional_button("Save", "primary")
        save_button.clicked.connect(self.accept)
        cancel_button = create_professional_button("Cancel", "secondary")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_assessment_data(self):
        return {
            "assessed_by": self.assessed_by_edit.text(),
            "assessment_date": self.assessment_date_edit.date().toString("yyyy-MM-dd"),
            "result": self.result_combo.currentText(),
        }
