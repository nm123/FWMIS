"""
General theming utilities.
"""

from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem

from .theme_styles_utils import get_main_stylesheet

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


def apply_theme(dialog):
    """Apply the professional theme to a dialog"""
    dialog.setStyleSheet(get_main_stylesheet())


def setup_professional_table(table, headers=None, emojis=None):
    """Setup a professional table with proper styling and headers"""
    if headers:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

    if emojis:
        # Add emojis to headers if provided
        header = table.horizontalHeader()
        for i, emoji in enumerate(emojis):
            if i < len(headers):
                current_text = headers[i]
                table.setHorizontalHeaderItem(
                    i, QTableWidgetItem(f"{emoji} {current_text}")
                )

    # Professional corporate styling
    table.setStyleSheet(
        f"""
        QTableWidget {{
            gridline-color: {COLORS['border']};
            selection-background-color: {COLORS['primary']};
            selection-color: white;
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['background']};
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }}
        QHeaderView::section {{
            background-color: {COLORS['surface']};
            padding: 10px 8px;
            border: 1px solid {COLORS['border']};
            font-weight: 600;
            color: {COLORS['dark']};
            font-size: 14px;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }}
        QTableWidget::item {{
            padding: 10px 8px;
            border-bottom: 1px solid {COLORS['border']};
            font-size: 14px;
            color: {COLORS['dark']};
        }}
        QTableWidget::item:selected {{
            background-color: {COLORS['primary']};
            color: white;
        }}
        QTableWidget::item:hover {{
            background-color: {COLORS['surface']};
        }}
    """
    )

    # Set default row height for better button display
    table.verticalHeader().setDefaultSectionSize(60)
