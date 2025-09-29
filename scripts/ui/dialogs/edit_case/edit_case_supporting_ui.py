"""
Supporting evidence and additional info UI setup for EditCaseDialog.
Handles BAS fields, supporting evidence, and additional information components.
"""

from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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

    # Criminal Charges Laid
    dialog_instance.criminal_charges_combo = NoWheelComboBox()
    dialog_instance.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.criminal_charges_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Criminal Charges Laid:", dialog_instance.criminal_charges_combo
    )

    # Disciplinary Charges
    dialog_instance.disciplinary_combo = NoWheelComboBox()
    dialog_instance.disciplinary_combo.addItems(["N/A", "Yes", "No"])
    dialog_instance.disciplinary_combo.setCurrentText("N/A")
    additional_layout.addRow(
        "Disciplinary Charges:", dialog_instance.disciplinary_combo
    )

    # Steps to prevent future occurrence
    dialog_instance.prevention_steps_edit = QTextEdit()
    dialog_instance.prevention_steps_edit.setMinimumHeight(40)
    dialog_instance.prevention_steps_edit.setMaximumHeight(
        40
    )  # Force height to prevent overrides
    additional_layout.addRow(
        "Steps taken to prevent future occurrence of F&W expenditure:",
        dialog_instance.prevention_steps_edit,
    )

    dialog_instance.main_layout.addWidget(additional_group)

    # ===== RECOVERY IN PROGRESS GROUP =====
    recovery_group = QGroupBox("Recovery in Progress")
    recovery_main_layout = QVBoxLayout(recovery_group)

    # Top row: Recovery Status (top left)
    status_layout = QHBoxLayout()
    dialog_instance.loss_recovery_status_label = QLabel("N/A")
    dialog_instance.loss_recovery_status_label.setStyleSheet(
        "QLabel { font-weight: bold; color: #666; padding: 3px; border: 1px solid #ddd; background-color: #f9f9f9; }"
    )
    status_layout.addWidget(QLabel("Recovery Status:"))
    status_layout.addWidget(dialog_instance.loss_recovery_status_label)
    status_layout.addStretch()
    recovery_main_layout.addLayout(status_layout)

    # Vertical split: Left and Right columns
    split_layout = QHBoxLayout()

    # LEFT COLUMN: Debtor Information
    left_column = QWidget()
    left_layout = QFormLayout(left_column)
    left_layout.setContentsMargins(0, 0, 10, 0)  # Right margin for spacing

    dialog_instance.debtor_name_edit = QLineEdit()
    dialog_instance.debtor_name_edit.setPlaceholderText("Enter debtor name...")
    left_layout.addRow("Debtor Name:", dialog_instance.debtor_name_edit)

    dialog_instance.debtor_number_edit = QLineEdit()
    dialog_instance.debtor_number_edit.setPlaceholderText("Debtor ID...")
    left_layout.addRow("Debtor No:", dialog_instance.debtor_number_edit)

    dialog_instance.debt_number_edit = QLineEdit()
    dialog_instance.debt_number_edit.setPlaceholderText("Debt ID...")
    left_layout.addRow("Debt No:", dialog_instance.debt_number_edit)

    split_layout.addWidget(left_column)

    # RIGHT COLUMN: Amounts and Installments
    right_column = QWidget()
    right_layout = QFormLayout(right_column)
    right_layout.setContentsMargins(10, 0, 0, 0)  # Left margin for spacing

    # Original Amount
    dialog_instance.original_amount_label = QLabel("R 0.00")
    dialog_instance.original_amount_label.setStyleSheet(
        "QLabel { font-weight: bold; color: #2c5aa0; padding: 3px; border: 1px solid #ddd; background-color: #f0f8ff; }"
    )
    right_layout.addRow("Original Amount:", dialog_instance.original_amount_label)

    # Amount Paid
    dialog_instance.amount_paid_label = QLabel("R 0.00")
    dialog_instance.amount_paid_label.setStyleSheet(
        "QLabel { font-weight: bold; color: #2d7d32; padding: 3px; border: 1px solid #ddd; background-color: #f1f8e9; }"
    )
    right_layout.addRow("Amount Paid:", dialog_instance.amount_paid_label)

    # Remaining Amount
    dialog_instance.remaining_amount_label = QLabel("R 0.00")
    dialog_instance.remaining_amount_label.setStyleSheet(
        "QLabel { font-weight: bold; color: #d32f2f; padding: 3px; border: 1px solid #ddd; background-color: #ffebee; }"
    )
    right_layout.addRow("Remaining:", dialog_instance.remaining_amount_label)

    # New Installment Amount
    dialog_instance.new_installment_amount_edit = QLineEdit()
    dialog_instance.new_installment_amount_edit.setPlaceholderText("0.00")
    dialog_instance.new_installment_amount_edit.setFixedWidth(100)
    right_layout.addRow("New Installment:", dialog_instance.new_installment_amount_edit)

    # Installment Date
    installment_date_layout = QHBoxLayout()
    dialog_instance.new_installment_date_edit = QLineEdit()
    dialog_instance.new_installment_date_edit.setPlaceholderText("YYYY-MM-DD")
    dialog_instance.new_installment_date_edit.setFixedWidth(100)
    dialog_instance.new_installment_date_button = QPushButton("...")
    dialog_instance.new_installment_date_button.setFixedWidth(25)
    dialog_instance.new_installment_date_button.clicked.connect(
        dialog_instance.select_new_installment_date
    )
    installment_date_layout.addWidget(dialog_instance.new_installment_date_edit)
    installment_date_layout.addWidget(dialog_instance.new_installment_date_button)
    installment_date_layout.addStretch()
    right_layout.addRow("Installment Date:", installment_date_layout)

    split_layout.addWidget(right_column)
    recovery_main_layout.addLayout(split_layout)

    # Action buttons row
    button_layout = QHBoxLayout()
    dialog_instance.add_installment_button = QPushButton("Add Installment")
    dialog_instance.add_installment_button.setStyleSheet(
        "QPushButton { padding: 4px 8px; font-size: 11px; }"
    )
    dialog_instance.add_installment_button.clicked.connect(
        dialog_instance.add_new_installment
    )
    button_layout.addWidget(dialog_instance.add_installment_button)

    dialog_instance.view_history_button = QPushButton("View History")
    dialog_instance.view_history_button.setStyleSheet(
        "QPushButton { padding: 4px 8px; font-size: 11px; }"
    )
    dialog_instance.view_history_button.clicked.connect(
        dialog_instance.view_installment_history
    )
    button_layout.addWidget(dialog_instance.view_history_button)
    button_layout.addStretch()
    recovery_main_layout.addLayout(button_layout)

    # Recovery Evidence at the bottom
    recovery_evidence_layout = QHBoxLayout()
    dialog_instance.recovery_evidence_rip_label = QLabel("Recovery Evidence:")
    dialog_instance.recovery_evidence_rip_edit = QLineEdit()
    dialog_instance.recovery_evidence_rip_button = QPushButton("Browse")
    dialog_instance.recovery_evidence_rip_button.clicked.connect(
        dialog_instance.browse_recovery_evidence_rip
    )
    dialog_instance.recovery_evidence_rip_view_button = QPushButton("View")
    dialog_instance.recovery_evidence_rip_view_button.clicked.connect(
        dialog_instance.view_recovery_evidence_rip
    )
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_rip_label)
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_rip_edit)
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_rip_button)
    recovery_evidence_layout.addWidget(
        dialog_instance.recovery_evidence_rip_view_button
    )
    recovery_main_layout.addLayout(recovery_evidence_layout)

    # Store reference to recovery group for conditional visibility
    dialog_instance.recovery_group = recovery_group

    # Set recovery group to hidden by default
    recovery_group.setVisible(False)

    dialog_instance.main_layout.addWidget(recovery_group)


# End of File
