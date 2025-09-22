"""
General theming utilities.
"""

from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem

from .theme_styles_utils import get_main_stylesheet

# Professional Color Palette
COLORS = {
    "primary": "#007bff",  # Blue - Primary actions
    "success": "#28a745",  # Green - Success states
    "warning": "#fd7e14",  # Orange - Warning states
    "danger": "#dc3545",  # Red - Danger/error states
    "info": "#17a2b8",  # Cyan - Information
    "secondary": "#6c757d",  # Gray - Secondary actions
    "light": "#f8f9fa",  # Light background
    "dark": "#343a40",  # Dark text
    "muted": "#6c757d",  # Muted text
    "border": "#dee2e6",  # Border color
    "hover": "#0056b3",  # Primary hover
    "success_hover": "#218838",  # Success hover
    "warning_hover": "#e8680f",  # Warning hover
    "danger_hover": "#c82333",  # Danger hover
    "info_hover": "#138496",  # Info hover
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

    # Professional styling
    table.setStyleSheet(
        f"""
        QTableWidget {{
            gridline-color: {COLORS['border']};
            selection-background-color: {COLORS['primary']};
            selection-color: white;
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            background-color: white;
        }}
        QHeaderView::section {{
            background-color: #f8f9fa;
            padding: 8px;
            border: 1px solid {COLORS['border']};
            font-weight: 600;
            color: {COLORS['dark']};
            font-size: 12px;
        }}
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
        }}
        QTableWidget::item:selected {{
            background-color: {COLORS['primary']};
            color: white;
        }}
    """
    )

    # Set default row height for better button display
    table.verticalHeader().setDefaultSectionSize(60)
