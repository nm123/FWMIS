"""
FWMIS Professional UI Theme Configuration

This module centralizes styling helpers so dialogs can share a consistent,
professional look. Import the utilities exposed here to apply the theme and to
obtain components with standardized styling.

Example::

    from scripts.Utilities.ui_theme import apply_theme, get_button_style

    apply_theme(dialog)
    button_style = get_button_style("primary")
"""

# Import from utility modules
from .button_theme_utils import create_professional_button, get_button_style
from .general_theme_utils import apply_theme, setup_professional_table
from .label_theme_utils import create_status_label, get_status_style
from .theme_components_utils import (create_action_button_row, create_form_row,
                                     create_professional_groupbox)
from .theme_styles_utils import get_groupbox_style, get_main_stylesheet

__all__ = [
    "COLORS",
    "apply_theme",
    "create_professional_button",
    "create_professional_groupbox",
    "create_status_label",
    "create_action_button_row",
    "create_form_row",
    "get_button_style",
    "get_status_style",
    "setup_professional_table",
    "get_groupbox_style",
    "get_main_stylesheet",
]

# Corporate Professional Color Palette
COLORS = {
    # Corporate Primary Colors
    "primary": "#1a365d",  # Deep Navy - Primary actions and headers
    "primary_light": "#2c5282",  # Lighter Navy - Hover states
    "primary_dark": "#153a5e",  # Darker Navy - Active states
    
    # Professional Status Colors
    "success": "#38a169",  # Professional Green - Success states
    "warning": "#d69e2e",  # Corporate Amber - Warning states
    "danger": "#e53e3e",  # Professional Red - Error states
    "info": "#3182ce",  # Corporate Blue - Information
    
    # Corporate Neutral Palette
    "secondary": "#4a5568",  # Charcoal Gray - Secondary actions
    "light": "#f7fafc",  # Clean White - Light backgrounds
    "dark": "#2d3748",  # Dark Gray - Primary text
    "muted": "#718096",  # Muted Gray - Secondary text
    "border": "#e2e8f0",  # Light Gray - Borders and dividers
    
    # Professional Backgrounds
    "background": "#ffffff",  # Pure White - Main background
    "surface": "#f7fafc",  # Light Gray - Surface backgrounds
    "elevated": "#ffffff",  # White - Elevated surfaces
    
    # Hover States
    "hover": "#2c5282",  # Navy hover
    "success_hover": "#2f855a",  # Green hover
    "warning_hover": "#b7791f",  # Amber hover
    "danger_hover": "#c53030",  # Red hover
    "info_hover": "#2b6cb0",  # Blue hover
    
    # Corporate Accents
    "accent": "#3182ce",  # Corporate Blue - Accent elements
    "accent_light": "#63b3ed",  # Light Blue - Light accents
    "accent_dark": "#2c5282",  # Dark Blue - Dark accents
}
