"""
List status UI setup for EditCaseDialog.
Handles list status information components.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QGridLayout, QGroupBox, QLabel, QVBoxLayout,
                             QWidget)


def setup_list_status_ui_components(dialog_instance):
    """
    Set up list status UI components.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # ===== LIST STATUS INFORMATION GROUP =====
    list_status_group = QGroupBox("List Status Information")
    list_status_layout = QVBoxLayout(list_status_group)

    # Create a simple grid layout for reliable text display
    dialog_instance.list_status_grid_widget = QWidget()
    grid_layout = QGridLayout(dialog_instance.list_status_grid_widget)
    grid_layout.setContentsMargins(10, 10, 10, 10)
    grid_layout.setSpacing(5)

    # Headers
    headers = [
        "Checklist",
        "Lead Schedule",
        "Recovered",
        "Write-Off Recommended",
        "Written Off",
        "Deleted Cases",
    ]

    # Initialize status labels list to store references for dynamic updates
    dialog_instance.status_labels = []

    # Add headers (row 0)
    for i, header in enumerate(headers):
        header_label = QLabel(header)
        header_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 8px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                text-align: center;
            }
        """
        )
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setMinimumHeight(40)
        grid_layout.addWidget(header_label, 0, i)

    # Add status value labels (row 1) - store references for updates
    for i, header in enumerate(headers):
        status_label = QLabel("N/A")  # Default to N/A; will be updated dynamically
        status_label.setStyleSheet(
            """
            QLabel {
                padding: 8px;
                border: 1px solid #ddd;
                text-align: center;
                background-color: white;
            }
        """
        )
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setMinimumHeight(40)
        status_label.setWordWrap(True)  # Allow text to wrap if needed
        grid_layout.addWidget(status_label, 1, i)
        dialog_instance.status_labels.append(status_label)  # Store reference

    list_status_layout.addWidget(dialog_instance.list_status_grid_widget)
    dialog_instance.main_layout.addWidget(list_status_group)


# End of File
