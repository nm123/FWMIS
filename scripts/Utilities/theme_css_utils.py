"""
Theme CSS utilities.
"""

from .theme_colors_utils import COLORS


def get_main_stylesheet():
    """Get the main application stylesheet with professional theming"""
    return f"""
        /* Main Application Styles */
        QDialog {{
            background-color: {COLORS['light']};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}

        /* Group Box Styling */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {COLORS['border']};
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
            padding-top: 10px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: {COLORS['dark']};
            font-size: 14px;
            font-weight: 600;
        }}

        /* Label Styling */
        QLabel {{
            color: {COLORS['dark']};
            font-size: 14px;
            font-weight: 500;
        }}

        /* Form Layout Label Alignment */
        QFormLayout QLabel {{
            text-align: left;
            vertical-align: middle;
            padding-top: 8px;
            padding-bottom: 8px;
        }}

        /* Input Field Styling */
        QLineEdit, QDateEdit, QComboBox {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 8px 12px;
            background-color: white;
            font-size: 14px;
            min-height: 24px;
        }}

        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{
            border-color: {COLORS['primary']};
            background-color: #f8f9ff;
            outline: none;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }}

        /* Button Styling */
        QPushButton {{
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            min-width: 80px;
            min-height: 24px;
        }}

        QPushButton:enabled {{
            background-color: {COLORS['primary']};
            color: white;
        }}

        QPushButton:enabled:hover {{
            background-color: {COLORS['hover']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['primary']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['secondary']};
            color: #adb5bd;
        }}

        /* Table Styling */
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
            font-size: 14px;
        }}

        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
            font-size: 14px;
        }}

        QTableWidget::item:selected {{
            background-color: {COLORS['primary']};
            color: white;
        }}

        /* Progress Bar Styling */
        QProgressBar {{
            border: 2px solid {COLORS['border']};
            border-radius: 4px;
            text-align: center;
            background-color: {COLORS['light']};
            min-height: 25px;
        }}

        QProgressBar::chunk {{
            background-color: {COLORS['primary']};
            border-radius: 2px;
        }}

        /* Scroll Bar Styling */
        QScrollBar:vertical {{
            border: none;
            background-color: {COLORS['light']};
            width: 14px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS['muted']};
            border-radius: 7px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['secondary']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        /* Status Message Styling */
        .status-info {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 4px;
            padding: 10px;
            color: #0c5460;
            font-size: 13px;
            font-weight: 500;
        }}

        .status-success {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            padding: 10px;
            color: #155724;
            font-size: 13px;
            font-weight: 500;
        }}

        .status-warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            color: #856404;
            font-size: 13px;
            font-weight: 500;
        }}

        .status-error {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 10px;
            color: #721c24;
            font-size: 13px;
            font-weight: 500;
        }}
    """


def get_groupbox_style(theme="default"):
    """Get group box style based on theme"""
    if theme == "blue":
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {COLORS['primary']};
                font-size: 14px;
            }}
        """
    elif theme == "green":
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['success']};
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {COLORS['success']};
                font-size: 14px;
            }}
        """
    elif theme == "purple":
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid #6f42c1;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #6f42c1;
                font-size: 14px;
            }}
        """
    elif theme == "red":
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['danger']};
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {COLORS['danger']};
                font-size: 14px;
            }}
        """
    else:  # default
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {COLORS['dark']};
                font-size: 14px;
            }}
        """
