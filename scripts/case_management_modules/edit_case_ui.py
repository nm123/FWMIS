from PyQt5.QtCore import QDate, QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

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


def setup_edit_ui(dialog):
    """Setup the UI for the EditCaseDialog"""
    # Apply professional theme
    apply_theme(dialog)

    # Create main layout
    layout = QVBoxLayout(dialog)

    # Form layout for fields
    form_layout = QFormLayout()

    # Responsibility field
    responsibility_layout = QHBoxLayout()
    dialog.responsibility_edit = QLineEdit()
    dialog.responsibility_edit.setReadOnly(True)
    dialog.responsibility_edit.setPlaceholderText(
        "Click Select to choose responsibility..."
    )
    responsibility_layout.addWidget(dialog.responsibility_edit)

    dialog.select_responsibility_button = create_professional_button(
        "Select", "secondary"
    )
    responsibility_layout.addWidget(dialog.select_responsibility_button)

    form_layout.addRow("Responsibility:", responsibility_layout)

    # Date fields (improved grid layout for better alignment)
    date_group = QWidget()
    date_layout = QGridLayout(date_group)
    date_layout.setContentsMargins(0, 0, 0, 0)
    date_layout.setSpacing(10)

    # Date Incurred
    date_incurred_label = QLabel("Date Incurred:")
    date_incurred_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_incurred_label, 0, 0)
    dialog.date_incurred_edit = QDateEdit(QDate.currentDate())
    dialog.date_incurred_edit.setCalendarPopup(True)
    dialog.date_incurred_edit.setFixedWidth(120)
    date_layout.addWidget(dialog.date_incurred_edit, 0, 1)

    # Date Identified
    date_identified_label = QLabel("Date Identified:")
    date_identified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_identified_label, 0, 2)
    dialog.date_identified_edit = QDateEdit(QDate.currentDate())
    dialog.date_identified_edit.setCalendarPopup(True)
    dialog.date_identified_edit.setFixedWidth(120)
    date_layout.addWidget(dialog.date_identified_edit, 0, 3)

    # Date Reported
    date_reported_label = QLabel("Date Reported:")
    date_reported_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    date_layout.addWidget(date_reported_label, 0, 4)
    dialog.date_reported_edit = QDateEdit(QDate.currentDate())
    dialog.date_reported_edit.setCalendarPopup(True)
    dialog.date_reported_edit.setFixedWidth(120)
    date_layout.addWidget(dialog.date_reported_edit, 0, 5)

    form_layout.addRow("Dates:", date_group)

    # Description
    dialog.description_edit = QTextEdit()
    dialog.description_edit.setMinimumHeight(80)
    form_layout.addRow("Description:", dialog.description_edit)

    # Category
    dialog.category_combo = NoWheelComboBox()
    dialog.category_combo.addItems([c["name"] for c in dialog.categories])
    form_layout.addRow("Category:", dialog.category_combo)

    # List
    dialog.list_combo = NoWheelComboBox()
    system_lists = [
        l["name"]
        for l in dialog.lists
        if l.get("is_system", False) and l["name"] != "Deleted Cases"
    ]
    dialog.list_combo.addItems(system_lists)
    # Select default list
    if system_lists:
        default_list = next(
            (l for l in dialog.lists if l.get("is_default", False)), None
        )
        if default_list and default_list["name"] in system_lists:
            dialog.list_combo.setCurrentText(default_list["name"])
    form_layout.addRow("List:", dialog.list_combo)

    # Status
    dialog.status_combo = NoWheelComboBox()
    # Status options will be set dynamically based on list selection
    dialog.status_combo.setCurrentText("Alleged")
    form_layout.addRow("Status:", dialog.status_combo)

    # Criminal Charges Laid
    dialog.criminal_charges_combo = NoWheelComboBox()
    dialog.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
    dialog.criminal_charges_combo.setCurrentText("N/A")
    form_layout.addRow("Criminal Charges Laid:", dialog.criminal_charges_combo)

    # Disciplinary process
    dialog.disciplinary_combo = NoWheelComboBox()
    dialog.disciplinary_combo.addItems(["N/A", "Yes", "No"])
    dialog.disciplinary_combo.setCurrentText("N/A")
    form_layout.addRow(
        "Disciplinary process in progress or completed:", dialog.disciplinary_combo
    )

    # Loss recovery - now handled by recovery progress system in supporting UI

    # Steps to prevent future occurrence
    dialog.prevention_steps_edit = QTextEdit()
    dialog.prevention_steps_edit.setMinimumHeight(40)
    form_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog.prevention_steps_edit,
    )

    # Amount
    dialog.amount_edit = QLineEdit()
    form_layout.addRow("Amount:", dialog.amount_edit)

    # BAS Payment fields
    dialog.bas_label = QLabel("BAS Payment No:")
    dialog.bas_payment_no_edit = QLineEdit()
    form_layout.addRow(dialog.bas_label, dialog.bas_payment_no_edit)

    dialog.bas_date_label = QLabel("BAS Payment Date:")
    dialog.bas_payment_date_edit = QDateEdit(QDate.currentDate())
    dialog.bas_payment_date_edit.setCalendarPopup(True)
    form_layout.addRow(dialog.bas_date_label, dialog.bas_payment_date_edit)

    # Persal No field
    dialog.persal_label = QLabel("Persal No:")
    dialog.persal_no_edit = QLineEdit()
    form_layout.addRow(dialog.persal_label, dialog.persal_no_edit)

    # File selection fields
    dialog.source_doc_label = QLabel("Source Document:")
    dialog.source_doc_edit = QLineEdit()
    dialog.source_doc_button = create_professional_button("Browse", "secondary")
    source_doc_layout = QHBoxLayout()
    source_doc_layout.addWidget(dialog.source_doc_edit)
    source_doc_layout.addWidget(dialog.source_doc_button)
    form_layout.addRow(dialog.source_doc_label, source_doc_layout)

    dialog.minutes_label = QLabel("Loss Control Minutes:")
    dialog.minutes_edit = QLineEdit()
    dialog.minutes_button = create_professional_button("Browse", "secondary")
    minutes_layout = QHBoxLayout()
    minutes_layout.addWidget(dialog.minutes_edit)
    minutes_layout.addWidget(dialog.minutes_button)
    form_layout.addRow(dialog.minutes_label, minutes_layout)

    dialog.evidence_label = QLabel("Assessment Evidence:")
    dialog.evidence_edit = QLineEdit()
    dialog.evidence_button = create_professional_button("Browse", "secondary")
    evidence_layout = QHBoxLayout()
    evidence_layout.addWidget(dialog.evidence_edit)
    evidence_layout.addWidget(dialog.evidence_button)
    form_layout.addRow(dialog.evidence_label, evidence_layout)

    # Assessment fields
    dialog.assessed_by_label = QLabel("Assessed By:")
    dialog.assessed_by_edit = QLineEdit()
    form_layout.addRow(dialog.assessed_by_label, dialog.assessed_by_edit)

    dialog.assessment_date_label = QLabel("Assessment Date:")
    dialog.assessment_date_edit = QDateEdit(QDate.currentDate())
    dialog.assessment_date_edit.setCalendarPopup(True)
    form_layout.addRow(dialog.assessment_date_label, dialog.assessment_date_edit)

    layout.addLayout(form_layout)

    # Buttons
    button_layout = QHBoxLayout()
    dialog.save_button = create_professional_button("Save Changes", "primary")
    dialog.delete_button = create_professional_button("Delete Case", "danger")
    dialog.cancel_button = create_professional_button("Cancel", "secondary")

    button_layout.addWidget(dialog.save_button)
    button_layout.addWidget(dialog.delete_button)
    button_layout.addStretch()
    button_layout.addWidget(dialog.cancel_button)
    layout.addLayout(button_layout)

    # Case No (read-only)
    dialog.trans_no_edit = QLineEdit(dialog.transaction_no)
    dialog.trans_no_edit.setReadOnly(True)
    form_layout.insertRow(0, "Case No:", dialog.trans_no_edit)

    dialog.setLayout(layout)
