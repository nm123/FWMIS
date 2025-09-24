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

    # BAS Payment No and Date in one row
    bas_payment_layout = QHBoxLayout()
    
    dialog_instance.bas_payment_no_edit = QLineEdit()
    bas_payment_layout.addWidget(dialog_instance.bas_payment_no_edit)
    
    # BAS Payment Date with manual date picker
    dialog_instance.bas_payment_date_edit = QLineEdit()
    dialog_instance.bas_payment_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.bas_payment_date_button = QPushButton("...")
    dialog_instance.bas_payment_date_button.setFixedWidth(30)
    dialog_instance.bas_payment_date_button.clicked.connect(
        dialog_instance.select_bas_payment_date
    )
    bas_payment_layout.addWidget(QLabel("Date:"))
    bas_payment_layout.addWidget(dialog_instance.bas_payment_date_edit)
    bas_payment_layout.addWidget(dialog_instance.bas_payment_date_button)
    
    supporting_layout.addRow("BAS Payment No:", bas_payment_layout)

    # BAS Journal No and Date in one row
    bas_journal_layout = QHBoxLayout()
    
    dialog_instance.bas_journal_no_edit = QLineEdit()
    bas_journal_layout.addWidget(dialog_instance.bas_journal_no_edit)
    
    # BAS Journal Date with manual date picker
    dialog_instance.bas_journal_date_edit = QLineEdit()
    dialog_instance.bas_journal_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.bas_journal_date_button = QPushButton("...")
    dialog_instance.bas_journal_date_button.setFixedWidth(30)
    dialog_instance.bas_journal_date_button.clicked.connect(
        dialog_instance.select_bas_journal_date
    )
    bas_journal_layout.addWidget(QLabel("Date:"))
    bas_journal_layout.addWidget(dialog_instance.bas_journal_date_edit)
    bas_journal_layout.addWidget(dialog_instance.bas_journal_date_button)
    
    supporting_layout.addRow("BAS Journal No:", bas_journal_layout)

    # Persal No field (conditional on HR Related category)
    dialog_instance.persal_label = QLabel("Persal No:")
    dialog_instance.persal_no_edit = QLineEdit()
    supporting_layout.addRow(
        dialog_instance.persal_label, dialog_instance.persal_no_edit
    )
    
    # Hide Persal No field by default - will be shown only for HR Related category
    dialog_instance.persal_label.setVisible(False)
    dialog_instance.persal_no_edit.setVisible(False)

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

    # Criminal Charges and Disciplinary process in one row
    charges_disciplinary_layout = QHBoxLayout()
    
    dialog_instance.criminal_charges_combo = NoWheelComboBox()
    dialog_instance.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.criminal_charges_combo.setCurrentText("N/A")
    charges_disciplinary_layout.addWidget(QLabel("Criminal Charges Laid:"))
    charges_disciplinary_layout.addWidget(dialog_instance.criminal_charges_combo)
    
    dialog_instance.disciplinary_combo = NoWheelComboBox()
    dialog_instance.disciplinary_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.disciplinary_combo.setCurrentText("N/A")
    charges_disciplinary_layout.addWidget(QLabel("Disciplinary process:"))
    charges_disciplinary_layout.addWidget(dialog_instance.disciplinary_combo)
    
    additional_layout.addRow("Charges/Disciplinary:", charges_disciplinary_layout)

    # Loss recovery
    dialog_instance.loss_recovery_combo = NoWheelComboBox()
    dialog_instance.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.loss_recovery_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Loss recovery commenced or completed:", dialog_instance.loss_recovery_combo
    )

    # Recovery in Progress fields (conditional)
    dialog_instance.debtor_name_edit = QLineEdit()
    dialog_instance.debtor_name_edit.setPlaceholderText("Enter debtor name...")
    additional_layout.addRow("Debtor Name:", dialog_instance.debtor_name_edit)

    dialog_instance.debt_number_edit = QLineEdit()
    dialog_instance.debt_number_edit.setPlaceholderText("Enter debt number...")
    additional_layout.addRow("Debt Number:", dialog_instance.debt_number_edit)

    # Latest installment amount and date in one row
    installment_layout = QHBoxLayout()
    
    dialog_instance.latest_installment_amount_edit = QLineEdit()
    dialog_instance.latest_installment_amount_edit.setPlaceholderText("0.00")
    installment_layout.addWidget(dialog_instance.latest_installment_amount_edit)
    
    dialog_instance.latest_installment_date_edit = QLineEdit()
    dialog_instance.latest_installment_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.latest_installment_date_button = QPushButton("...")
    dialog_instance.latest_installment_date_button.setFixedWidth(30)
    dialog_instance.latest_installment_date_button.clicked.connect(
        dialog_instance.select_latest_installment_date
    )
    installment_layout.addWidget(QLabel("Date:"))
    installment_layout.addWidget(dialog_instance.latest_installment_date_edit)
    installment_layout.addWidget(dialog_instance.latest_installment_date_button)
    
    additional_layout.addRow("Latest Installment Amount:", installment_layout)

    # Total recovered amount (read-only, calculated)
    dialog_instance.total_recovered_amount_edit = QLineEdit()
    dialog_instance.total_recovered_amount_edit.setReadOnly(True)
    dialog_instance.total_recovered_amount_edit.setPlaceholderText("0.00")
    additional_layout.addRow("Total Recovered Amount:", dialog_instance.total_recovered_amount_edit)

    # Steps to prevent future occurrence
    dialog_instance.prevention_steps_edit = QTextEdit()
    dialog_instance.prevention_steps_edit.setMinimumHeight(40)
    dialog_instance.prevention_steps_edit.setMaximumHeight(40)  # Force height to prevent overrides
    additional_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog_instance.prevention_steps_edit,
    )

    dialog_instance.main_layout.addWidget(additional_group)


# End of File
