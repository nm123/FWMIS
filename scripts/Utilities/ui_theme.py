"""
FWMIS Professional UI Theme Configuration

This module provides centralized styling and layout patterns for consistent UI across the entire application.
All dialogs and components should import and use these styles for a professional, cohesive user experience.

Usage:
    from scripts.Utilities.ui_theme import apply_theme, get_button_style, get_groupbox_style

    # Apply theme to dialog
    apply_theme(dialog)

    # Get specific styles
    button_style = get_button_style('primary')
    group_style = get_groupbox_style('blue')
"""

from PyQt5.QtWidgets import QDialog, QGroupBox, QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox, QTableWidget, QTableWidgetItem, QProgressBar
from PyQt5.QtCore import Qt

# Import from utility modules
from .button_theme_utils import get_button_style, create_professional_button
from .label_theme_utils import get_status_style, create_status_label
from .general_theme_utils import apply_theme, setup_professional_table
from .theme_styles_utils import get_groupbox_style, get_main_stylesheet
from .theme_components_utils import create_professional_groupbox, create_form_row, create_action_button_row


# Professional Color Palette
COLORS = {
    'primary': '#007bff',      # Blue - Primary actions
    'success': '#28a745',      # Green - Success states
    'warning': '#fd7e14',      # Orange - Warning states
    'danger': '#dc3545',       # Red - Danger/error states
    'info': '#17a2b8',         # Cyan - Information
    'secondary': '#6c757d',    # Gray - Secondary actions
    'light': '#f8f9fa',        # Light background
    'dark': '#343a40',         # Dark text
    'muted': '#6c757d',        # Muted text
    'border': '#dee2e6',       # Border color
    'hover': '#0056b3',        # Primary hover
    'success_hover': '#218838', # Success hover
    'warning_hover': '#e8680f', # Warning hover
    'danger_hover': '#c82333',  # Danger hover
    'info_hover': '#138496',   # Info hover
}

