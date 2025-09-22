"""
Attachments and buttons UI setup for EditCaseDialog.
Handles source document, attachments, and dialog buttons.
"""

from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout)
from scripts.Utilities.case_save_utils import save_case


def setup_attachments_ui_components(dialog_instance):
    """
    Set up attachments and buttons UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== FILE ATTACHMENTS GROUP =====
    attachments_group = QGroupBox("File Attachments")
    attachments_layout = QFormLayout(attachments_group)

    # Source Document
    dialog_instance.source_doc_label = QLabel("Source Document:")
    dialog_instance.source_doc_edit = QLineEdit()
    dialog_instance.source_doc_button = QPushButton("Browse")
    dialog_instance.source_doc_button.clicked.connect(dialog_instance.browse_source_doc)
    dialog_instance.source_doc_view_button = QPushButton("View")
    dialog_instance.source_doc_view_button.clicked.connect(
        dialog_instance.view_source_doc
    )
    source_doc_layout = QHBoxLayout()
    source_doc_layout.addWidget(dialog_instance.source_doc_edit)
    source_doc_layout.addWidget(dialog_instance.source_doc_button)
    source_doc_layout.addWidget(dialog_instance.source_doc_view_button)
    attachments_layout.addRow(dialog_instance.source_doc_label, source_doc_layout)

    dialog_instance.main_layout.addWidget(attachments_group)

    # Set up scroll area
    scroll_area = dialog_instance.scroll_area
    scroll_widget = dialog_instance.scroll_widget
    scroll_area.setWidget(scroll_widget)
    scroll_area.setWidgetResizable(True)
    dialog_instance.layout.addWidget(scroll_area)

    # Buttons
    button_layout = QHBoxLayout()
    dialog_instance.save_button = QPushButton("Save Changes")
    dialog_instance.save_button.clicked.connect(lambda: save_case(dialog_instance))

    dialog_instance.determination_button = QPushButton("Loss Control Determination")
    dialog_instance.determination_button.clicked.connect(
        dialog_instance.open_determination_dialog
    )
    dialog_instance.determination_button.setStyleSheet(
        "QPushButton { background-color: #2196F3; color: white; font-weight: bold; }"
    )

    dialog_instance.delete_button = QPushButton("Delete Case")
    dialog_instance.delete_button.clicked.connect(dialog_instance.delete_case)
    dialog_instance.delete_button.setStyleSheet(
        "QPushButton { color: red; font-weight: bold; }"
    )

    dialog_instance.cancel_button = QPushButton("Cancel")
    dialog_instance.cancel_button.clicked.connect(dialog_instance.reject)

    button_layout.addWidget(dialog_instance.save_button)
    button_layout.addWidget(dialog_instance.determination_button)
    button_layout.addWidget(dialog_instance.delete_button)
    button_layout.addStretch()
    button_layout.addWidget(dialog_instance.cancel_button)
    dialog_instance.layout.addLayout(button_layout)

    # Connect signals
    dialog_instance.category_combo.currentIndexChanged.connect(
        dialog_instance.schedule_update_conditional_fields
    )
    dialog_instance.assessment_status_combo.currentTextChanged.connect(
        dialog_instance.on_assessment_status_changed
    )
    dialog_instance.lc_status_combo.currentTextChanged.connect(
        dialog_instance.on_lc_status_changed
    )

    # Update determination button visibility
    dialog_instance.update_determination_button_visibility()


# End of File
