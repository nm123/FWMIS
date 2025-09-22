"""
Assessment UI setup for EditCaseDialog.
Handles assessment status and evidence components.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from scripts.ui.components.custom_widgets import NoWheelComboBox


def setup_assessment_ui_components(dialog_instance):
    """
    Set up assessment UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== ASSESSMENT GROUP =====
    assessment_group = QGroupBox("Assessment")
    assessment_layout = QFormLayout(assessment_group)

    # Assessment Status - label changes based on selected list
    status_label_text = (
        "Loss Control Status"
        if dialog_instance.selected_list == "Lead Schedule"
        else "Assessment Status"
    )
    dialog_instance.assessment_status_combo = NoWheelComboBox()
    dialog_instance.assessment_status_combo.addItems(
        ["Alleged", "Under Assessment", "Valid", "Confirmed"]
    )
    dialog_instance.assessment_status_combo.setCurrentText(
        dialog_instance.assessment_status
    )
    assessment_layout.addRow(
        status_label_text + ":", dialog_instance.assessment_status_combo
    )

    # Assessment Evidence (upload and display)
    dialog_instance.assessment_evidence_label = QLabel("Assessment Evidence")
    dialog_instance.assessment_evidence_edit = QLineEdit()
    dialog_instance.evidence_button = QPushButton("Browse")
    dialog_instance.evidence_button.clicked.connect(
        dialog_instance.browse_assessment_evidence
    )
    dialog_instance.view_assessment_evidence_button = QPushButton("View")
    dialog_instance.view_assessment_evidence_button.setFixedWidth(60)
    dialog_instance.view_assessment_evidence_button.clicked.connect(
        dialog_instance.view_assessment_evidence
    )
    evidence_layout = QHBoxLayout()
    evidence_layout.addWidget(dialog_instance.assessment_evidence_edit)
    evidence_layout.addWidget(dialog_instance.evidence_button)
    evidence_layout.addWidget(dialog_instance.view_assessment_evidence_button)

    # dialog_instance.assessment_required_label = QLabel("(REQUIRED)")
    # dialog_instance.assessment_required_label.setStyleSheet("color: red; font-weight: bold;")
    # evidence_layout.addWidget(dialog_instance.assessment_required_label)

    assessment_layout.addRow(dialog_instance.assessment_evidence_label, evidence_layout)

    dialog_instance.main_layout.addWidget(assessment_group)


# End of File
