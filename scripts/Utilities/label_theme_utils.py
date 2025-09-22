"""
Label and status theming utilities.
"""

from PyQt5.QtWidgets import QLabel

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


def get_status_style(status_type="info"):
    """Get status message style"""
    if status_type == "success":
        return f"""
            QLabel {{
                background-color: #d4edda;
                border: 2px solid #28a745;
                border-radius: 6px;
                padding: 12px;
                color: #155724;
                font-weight: bold;
                font-size: 13px;
                line-height: 1.4;
            }}
        """
    elif status_type == "warning":
        return f"""
            QLabel {{
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 6px;
                padding: 12px;
                color: #856404;
                font-weight: bold;
                font-size: 13px;
                line-height: 1.4;
            }}
        """
    elif status_type == "error":
        return f"""
            QLabel {{
                background-color: #f8d7da;
                border: 2px solid #dc3545;
                border-radius: 6px;
                padding: 12px;
                color: #721c24;
                font-weight: bold;
                font-size: 13px;
                line-height: 1.4;
            }}
        """
    else:  # info
        return f"""
            QLabel {{
                background-color: #d1ecf1;
                border: 2px solid #17a2b8;
                border-radius: 6px;
                padding: 12px;
                color: #0c5460;
                font-weight: bold;
                font-size: 13px;
                line-height: 1.4;
            }}
        """


def create_status_label(text, status_type="info"):
    """Create a professional status label"""
    label = QLabel(text)
    label.setStyleSheet(get_status_style(status_type))
    return label
