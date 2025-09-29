"""
UI Setup Module

Contains the UI initialization and setup logic for the main FWMIS application window.
This helps reduce the size of the main application file and improves maintainability.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_main import FWManagementApp


def setup_ui(app: "FWManagementApp") -> None:
    """
    Set up the main user interface for the FWMIS application.

    Args:
        app: The main FWManagementApp instance
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

    from scripts.Utilities.financial_utils import get_active_period_display
    from scripts.Utilities.ui_theme import create_professional_button

    # Create professional central widget
    central_widget = QWidget()
    app.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setSpacing(20)
    layout.setContentsMargins(30, 30, 30, 30)

    # Welcome header
    active_period_text = get_active_period_display()
    if active_period_text:
        welcome_text = f"Welcome to the FWMIS\n{active_period_text}"
    else:
        welcome_text = "Welcome to the FWMIS"

    welcome_label = QLabel(welcome_text)
    welcome_label.setWordWrap(True)
    welcome_label.setAlignment(Qt.AlignCenter)  # Center align the text within the label
    welcome_label.setStyleSheet(
        """
        QLabel {
            font-size: 24px;
            font-weight: 600;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            color: #1a365d;
            margin-bottom: 10px;
        }
    """
    )
    layout.addWidget(welcome_label, alignment=Qt.AlignCenter)

    # Subtitle
    subtitle_label = QLabel(
        "Fruitless and Wasteful Expenditure Management Information System"
    )
    subtitle_label.setAlignment(
        Qt.AlignCenter
    )  # Center align the text within the label
    subtitle_label.setStyleSheet(
        """
        QLabel {
            font-size: 16px;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            color: #4a5568;
            margin-bottom: 30px;
        }
    """
    )
    layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

    # Quick actions section
    actions_group = QWidget()
    actions_layout = QVBoxLayout(actions_group)
    actions_layout.setSpacing(15)

    actions_title = QLabel("Quick Actions")
    actions_title.setStyleSheet(
        """
        QLabel {
            font-size: 18px;
            font-weight: 600;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            color: #2d3748;
            margin-bottom: 15px;
        }
    """
    )
    actions_layout.addWidget(actions_title, alignment=Qt.AlignCenter)

    # Action buttons in a grid
    buttons_layout = QGridLayout()
    buttons_layout.setSpacing(15)

    # Create professional corporate action buttons
    add_case_btn = create_professional_button("Add New Case", "success", "large")
    add_case_btn.clicked.connect(app.add_new_case)
    buttons_layout.addWidget(add_case_btn, 0, 0)

    view_cases_btn = create_professional_button("View Cases", "primary", "large")
    view_cases_btn.clicked.connect(app.view_cases)
    buttons_layout.addWidget(view_cases_btn, 0, 1)

    import_cases_btn = create_professional_button("Import Cases", "info", "large")
    import_cases_btn.clicked.connect(app.import_undisclosed_cases)
    buttons_layout.addWidget(import_cases_btn, 1, 0)

    reports_btn = create_professional_button("Generate Reports", "warning", "large")
    reports_btn.clicked.connect(app.generate_reports)
    buttons_layout.addWidget(reports_btn, 1, 1)

    actions_layout.addLayout(buttons_layout)
    layout.addWidget(actions_group)

    # Add stretch to push everything to the top
    layout.addStretch()
