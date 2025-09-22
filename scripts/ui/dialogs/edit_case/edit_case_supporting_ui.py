"""
Supporting evidence and additional info UI setup for EditCaseDialog.
Handles BAS fields, supporting evidence, and additional information components.
"""

from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit)
from scripts.ui.components.custom_widgets import NoWheelComboBox


def setup_supporting_ui_components(dialog_instance):
    """
    Set up supporting evidence and additional info UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== SUPPORTING EVIDENCE GROUP =====
    supporting_group = QGroupBox("Supporting Evidence (To Prove Existence)")
    supporting_layout = QFormLayout(supporting_group)

    # BAS Payment fields
    dialog_instance.bas_label = QLabel("BAS Payment No:")
    dialog_instance.bas_payment_no_edit = QLineEdit()
    supporting_layout.addRow(
        dialog_instance.bas_label, dialog_instance.bas_payment_no_edit
    )

    # BAS Payment Date with manual date picker
    bas_payment_date_layout = QHBoxLayout()
    dialog_instance.bas_date_label = QLabel("BAS Payment Date:")
    dialog_instance.bas_payment_date_edit = QLineEdit()
    dialog_instance.bas_payment_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.bas_payment_date_button = QPushButton("...")
    dialog_instance.bas_payment_date_button.setFixedWidth(30)
    dialog_instance.bas_payment_date_button.clicked.connect(
        dialog_instance.select_bas_payment_date
    )
    bas_payment_date_layout.addWidget(dialog_instance.bas_payment_date_edit)
    bas_payment_date_layout.addWidget(dialog_instance.bas_payment_date_button)
    supporting_layout.addRow(dialog_instance.bas_date_label, bas_payment_date_layout)

    # BAS Journal fields
    dialog_instance.bas_journal_label = QLabel("BAS Journal No:")
    dialog_instance.bas_journal_no_edit = QLineEdit()
    supporting_layout.addRow(
        dialog_instance.bas_journal_label, dialog_instance.bas_journal_no_edit
    )

    # BAS Journal Date with manual date picker
    bas_journal_date_layout = QHBoxLayout()
    dialog_instance.bas_journal_date_label = QLabel("BAS Journal Date:")
    dialog_instance.bas_journal_date_edit = QLineEdit()
    dialog_instance.bas_journal_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.bas_journal_date_button = QPushButton("...")
    dialog_instance.bas_journal_date_button.setFixedWidth(30)
    dialog_instance.bas_journal_date_button.clicked.connect(
        dialog_instance.select_bas_journal_date
    )
    bas_journal_date_layout.addWidget(dialog_instance.bas_journal_date_edit)
    bas_journal_date_layout.addWidget(dialog_instance.bas_journal_date_button)
    supporting_layout.addRow(
        dialog_instance.bas_journal_date_label, bas_journal_date_layout
    )

    # Persal No field
    dialog_instance.persal_label = QLabel("Persal No:")
    dialog_instance.persal_no_edit = QLineEdit()
    supporting_layout.addRow(
        dialog_instance.persal_label, dialog_instance.persal_no_edit
    )

    # Supporting Evidence Document upload
    dialog_instance.supporting_evidence_label = QLabel("Supporting Evidence Document:")
    dialog_instance.supporting_evidence_edit = QLineEdit()
    dialog_instance.supporting_evidence_button = QPushButton("Browse")
    dialog_instance.supporting_evidence_button.clicked.connect(
        dialog_instance.browse_supporting_evidence
    )
    dialog_instance.supporting_evidence_view_button = QPushButton("View")
    dialog_instance.supporting_evidence_view_button.clicked.connect(
        dialog_instance.view_supporting_evidence
    )
    supporting_evidence_layout = QHBoxLayout()
    supporting_evidence_layout.addWidget(dialog_instance.supporting_evidence_edit)
    supporting_evidence_layout.addWidget(dialog_instance.supporting_evidence_button)
    supporting_evidence_layout.addWidget(
        dialog_instance.supporting_evidence_view_button
    )

    # dialog_instance.supporting_required_label = QLabel("(REQUIRED)")
    # dialog_instance.supporting_required_label.setStyleSheet("color: red; font-weight: bold;")
    # supporting_evidence_layout.addWidget(dialog_instance.supporting_required_label)

    supporting_layout.addRow(
        dialog_instance.supporting_evidence_label, supporting_evidence_layout
    )

    dialog_instance.main_layout.addWidget(supporting_group)

    # ===== ADDITIONAL INFORMATION GROUP =====
    additional_group = QGroupBox("Additional Information")
    additional_layout = QFormLayout(additional_group)

    # Criminal Charges Laid
    dialog_instance.criminal_charges_combo = NoWheelComboBox()
    dialog_instance.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.criminal_charges_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Criminal Charges Laid:", dialog_instance.criminal_charges_combo
    )

    # Disciplinary process
    dialog_instance.disciplinary_combo = NoWheelComboBox()
    dialog_instance.disciplinary_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.disciplinary_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Disciplinary process in progress or completed:",
        dialog_instance.disciplinary_combo,
    )

    # Loss recovery
    dialog_instance.loss_recovery_combo = NoWheelComboBox()
    dialog_instance.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.loss_recovery_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Loss recovery commenced or completed:", dialog_instance.loss_recovery_combo
    )

    # Steps to prevent future occurrence
    dialog_instance.prevention_steps_edit = QTextEdit()
    dialog_instance.prevention_steps_edit.setMinimumHeight(40)
    additional_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog_instance.prevention_steps_edit,
    )

    dialog_instance.main_layout.addWidget(additional_group)


# End of File
