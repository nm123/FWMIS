"""
Theme components utilities.
"""

from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QLabel

from .theme_styles_utils import get_groupbox_style


def create_professional_groupbox(title, theme='default'):
    """Create a professional group box with proper styling"""
    groupbox = QGroupBox(title)
    groupbox.setStyleSheet(get_groupbox_style(theme))
    return groupbox


def create_form_row(label_text, widget, tooltip=None):
    """Create a professional form row with label and widget"""
    layout = QHBoxLayout()
    layout.setSpacing(10)

    label = QLabel(label_text)
    label.setStyleSheet("font-weight: bold; min-width: 100px;")
    layout.addWidget(label)

    widget.setMinimumHeight(35)
    layout.addWidget(widget)

    if tooltip:
        widget.setToolTip(tooltip)

    layout.addStretch()
    return layout


def create_action_button_row(buttons):
    """Create a professional row of action buttons"""
    layout = QHBoxLayout()
    layout.setSpacing(12)

    for button in buttons:
        layout.addWidget(button)

    layout.addStretch()
    return layout