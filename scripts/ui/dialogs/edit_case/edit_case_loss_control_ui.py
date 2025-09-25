"""
Loss control UI setup for EditCaseDialog.
Handles loss control status, recovery evidence, and minutes components.
"""

from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from scripts.ui.components.custom_widgets import NoWheelComboBox


def setup_loss_control_ui_components(dialog_instance):
    """
    Set up loss control UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== LOSS CONTROL GROUP =====
    loss_control_group = QGroupBox("Loss Control Committee")
    loss_control_layout = QFormLayout(loss_control_group)

    # Loss Control Status (moved from Assessment group)
    dialog_instance.lc_status_combo = NoWheelComboBox()
    dialog_instance.lc_status_combo.addItems(
        ["Awaiting LC determination", "Recovery in Progress", "Recovered", "Write-Off Recommended"]
    )
    if dialog_instance.lc_status:
        dialog_instance.lc_status_combo.setCurrentText(dialog_instance.lc_status)
    loss_control_layout.addRow("Loss Control Status:", dialog_instance.lc_status_combo)

    # Recovery Evidence (conditional - shown for "Recovered" status)
    dialog_instance.recovery_evidence_label = QLabel("Recovery Evidence:")
    dialog_instance.recovery_evidence_edit = QLineEdit()
    dialog_instance.recovery_evidence_button = QPushButton("Browse")
    dialog_instance.recovery_evidence_button.clicked.connect(
        dialog_instance.browse_recovery_evidence
    )
    dialog_instance.recovery_evidence_view_button = QPushButton("View")
    dialog_instance.recovery_evidence_view_button.clicked.connect(
        dialog_instance.view_recovery_evidence
    )
    recovery_evidence_layout = QHBoxLayout()
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_edit)
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_button)
    recovery_evidence_layout.addWidget(dialog_instance.recovery_evidence_view_button)
    loss_control_layout.addRow(
        dialog_instance.recovery_evidence_label, recovery_evidence_layout
    )

    # Set recovery evidence fields to hidden by default; visibility controlled dynamically
    dialog_instance.recovery_evidence_label.setVisible(False)
    dialog_instance.recovery_evidence_edit.setVisible(False)
    dialog_instance.recovery_evidence_button.setVisible(False)
    dialog_instance.recovery_evidence_view_button.setVisible(False)

    # LC Minutes
    dialog_instance.minutes_label = QLabel("LC Minutes:")
    dialog_instance.minutes_edit = QLineEdit()
    dialog_instance.minutes_button = QPushButton("Browse")
    dialog_instance.minutes_button.clicked.connect(dialog_instance.browse_minutes)
    dialog_instance.minutes_view_button = QPushButton("View")
    dialog_instance.minutes_view_button.clicked.connect(dialog_instance.view_minutes)
    minutes_layout = QHBoxLayout()
    minutes_layout.addWidget(dialog_instance.minutes_edit)
    minutes_layout.addWidget(dialog_instance.minutes_button)
    minutes_layout.addWidget(dialog_instance.minutes_view_button)
    loss_control_layout.addRow(dialog_instance.minutes_label, minutes_layout)

    dialog_instance.main_layout.addWidget(loss_control_group)


# End of File
