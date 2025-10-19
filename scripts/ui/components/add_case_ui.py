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

    # Create main layout
    layout = QVBoxLayout(dialog)

    # Create scroll area for the form
    scroll_area = QScrollArea()
    scroll_widget = QWidget()
    form_layout = QFormLayout(scroll_widget)

    # Case Number (read-only)
    dialog.trans_no_edit = QLineEdit("To be assigned")
    dialog.trans_no_edit.setReadOnly(True)
    form_layout.addRow("Case No:", dialog.trans_no_edit)

    # Responsibility
    resp_layout = QHBoxLayout()
    dialog.responsibility_edit = QLineEdit()
    dialog.responsibility_edit.setReadOnly(True)
    dialog.responsibility_edit.setPlaceholderText(
        "Click Select to choose responsibility..."
    )
    resp_layout.addWidget(dialog.responsibility_edit)

    dialog.select_responsibility_button = create_professional_button(
        "Select", "secondary"
    )
    dialog.select_responsibility_button.clicked.connect(dialog.select_responsibility)
    resp_layout.addWidget(dialog.select_responsibility_button)

    form_layout.addRow("Responsibility:", resp_layout)

    # Description
    dialog.description_edit = QTextEdit()
    dialog.description_edit.setMinimumHeight(60)
    form_layout.addRow("Description:", dialog.description_edit)

    # Category
    dialog.category_combo = NoWheelComboBox()
    if dialog.categories:
        dialog.category_combo.addItems([c["name"] for c in dialog.categories])
    form_layout.addRow("Category:", dialog.category_combo)

    # Date Incurred
    dialog.date_incurred_edit = QDateEdit(QDate.currentDate())
    dialog.date_incurred_edit.setCalendarPopup(True)
    form_layout.addRow("Date Incurred:", dialog.date_incurred_edit)

    # Date Identified
    dialog.date_identified_edit = QDateEdit(QDate.currentDate())
    dialog.date_identified_edit.setCalendarPopup(True)
    form_layout.addRow("Date Identified:", dialog.date_identified_edit)

    # Date Reported
    dialog.date_reported_edit = QDateEdit(QDate.currentDate())
    dialog.date_reported_edit.setCalendarPopup(True)
    form_layout.addRow("Date Reported:", dialog.date_reported_edit)

    # List
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
    form_layout.addRow("List:", dialog.list_combo)

    # Status
    dialog.status_combo = NoWheelComboBox()
    dialog.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
    dialog.status_combo.setCurrentText("Alleged")
    form_layout.addRow("Status:", dialog.status_combo)

    # Amount
    dialog.amount_edit = QLineEdit()
    form_layout.addRow("Amount:", dialog.amount_edit)

    # Assessment Evidence
    file_layout = QHBoxLayout()
    dialog.file_path_edit = QLineEdit()
    dialog.file_path_edit.setPlaceholderText("Select file...")
    browse_button = create_professional_button("Browse...", "secondary")
    browse_button.clicked.connect(dialog.browse_file)
    file_layout.addWidget(dialog.file_path_edit)
    file_layout.addWidget(browse_button)
    form_layout.addRow("Assessment Evidence:", file_layout)

    # Supporting Evidence (To prove Existence)
    supporting_layout = QHBoxLayout()
    dialog.supporting_evidence_edit = QLineEdit()
    dialog.supporting_evidence_edit.setPlaceholderText("Select file (optional)...")
    supporting_browse_button = create_professional_button("Browse...", "secondary")
    supporting_browse_button.clicked.connect(dialog.browse_supporting_evidence)
    supporting_layout.addWidget(dialog.supporting_evidence_edit)
    supporting_layout.addWidget(supporting_browse_button)
    form_layout.addRow("Supporting Evidence (To prove Existence):", supporting_layout)

    # Conditional fields - add them but hide initially
    dialog.bas_label = QLabel("BAS Payment No:")
    dialog.bas_payment_no_edit = QLineEdit()
    dialog.bas_label.setVisible(False)
    dialog.bas_payment_no_edit.setVisible(False)
    form_layout.addRow(dialog.bas_label, dialog.bas_payment_no_edit)

    dialog.bas_date_label = QLabel("BAS Payment Date:")
    dialog.bas_payment_date_edit = QDateEdit(QDate.currentDate())
    dialog.bas_payment_date_edit.setCalendarPopup(True)
    dialog.bas_date_label.setVisible(False)
    dialog.bas_payment_date_edit.setVisible(False)
    form_layout.addRow(dialog.bas_date_label, dialog.bas_payment_date_edit)

    dialog.bas_journal_label = QLabel("BAS Journal No:")
    dialog.bas_journal_no_edit = QLineEdit()
    dialog.bas_journal_label.setVisible(False)
    dialog.bas_journal_no_edit.setVisible(False)
    form_layout.addRow(dialog.bas_journal_label, dialog.bas_journal_no_edit)

    dialog.bas_journal_date_label = QLabel("BAS Journal Date:")
    dialog.bas_journal_date_edit = QDateEdit(QDate.currentDate())
    dialog.bas_journal_date_edit.setCalendarPopup(True)
    dialog.bas_journal_date_label.setVisible(False)
    dialog.bas_journal_date_edit.setVisible(False)
    form_layout.addRow(dialog.bas_journal_date_label, dialog.bas_journal_date_edit)

    dialog.persal_label = QLabel("Persal No:")
    dialog.persal_no_edit = QLineEdit()
    dialog.persal_label.setVisible(False)
    dialog.persal_no_edit.setVisible(False)
    form_layout.addRow(dialog.persal_label, dialog.persal_no_edit)

    # Prevention steps
    dialog.prevention_steps_edit = QTextEdit()
    dialog.prevention_steps_edit.setMinimumHeight(40)
    form_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog.prevention_steps_edit,
    )

    # Assessment fields - add them but hide initially
    dialog.source_doc_label = QLabel("Source Document:")
    dialog.source_doc_edit = QLineEdit()
    dialog.source_doc_button = create_professional_button("Browse", "secondary")
    dialog.source_doc_button.clicked.connect(dialog.browse_source_doc)
    source_doc_layout = QHBoxLayout()
    source_doc_layout.addWidget(dialog.source_doc_edit)
    source_doc_layout.addWidget(dialog.source_doc_button)
    dialog.source_doc_label.setVisible(False)
    dialog.source_doc_edit.setVisible(False)
    dialog.source_doc_button.setVisible(False)
    form_layout.addRow(dialog.source_doc_label, source_doc_layout)

    dialog.minutes_label = QLabel("Loss Control Minutes:")
    dialog.minutes_edit = QLineEdit()
    dialog.minutes_button = create_professional_button("Browse", "secondary")
    dialog.minutes_button.clicked.connect(dialog.browse_minutes)
    minutes_layout = QHBoxLayout()
    minutes_layout.addWidget(dialog.minutes_edit)
    minutes_layout.addWidget(dialog.minutes_button)
    dialog.minutes_label.setVisible(False)
    dialog.minutes_edit.setVisible(False)
    dialog.minutes_button.setVisible(False)
    form_layout.addRow(dialog.minutes_label, minutes_layout)

    dialog.evidence_label = QLabel("Assessment Evidence:")
    dialog.evidence_edit = QLineEdit()
    dialog.evidence_button = create_professional_button("Browse", "secondary")
    dialog.evidence_button.clicked.connect(dialog.browse_evidence)
    evidence_layout = QHBoxLayout()
    evidence_layout.addWidget(dialog.evidence_edit)
    evidence_layout.addWidget(dialog.evidence_button)
    dialog.evidence_label.setVisible(False)
    dialog.evidence_edit.setVisible(False)
    dialog.evidence_button.setVisible(False)
    form_layout.addRow(dialog.evidence_label, evidence_layout)

    dialog.assessed_by_label = QLabel("Assessed By:")
    dialog.assessed_by_edit = QLineEdit()
    dialog.assessed_by_label.setVisible(False)
    dialog.assessed_by_edit.setVisible(False)
    form_layout.addRow(dialog.assessed_by_label, dialog.assessed_by_edit)

    dialog.assessment_date_label = QLabel("Assessment Date:")
    dialog.assessment_date_edit = QDateEdit(QDate.currentDate())
    dialog.assessment_date_edit.setCalendarPopup(True)
    dialog.assessment_date_label.setVisible(False)
    dialog.assessment_date_edit.setVisible(False)
    form_layout.addRow(dialog.assessment_date_label, dialog.assessment_date_edit)

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
