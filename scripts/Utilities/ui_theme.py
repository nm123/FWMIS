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
            font-size: 13px;
            font-weight: 500;
        }}

        /* Input Field Styling */
        QLineEdit, QDateEdit, QComboBox {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 8px 12px;
            background-color: white;
            font-size: 13px;
            min-height: 20px;
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
            font-size: 13px;
            font-weight: 500;
            border: none;
            min-width: 80px;
            min-height: 20px;
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


def get_button_style(button_type='primary', size='normal'):
    """Get button style based on type and size"""
    # Get size properties
    if size == 'large':
        padding = "14px 24px"
        font_size = "16px"
        min_width = "160px"
    elif size == 'small':
        padding = "6px 12px"
        font_size = "12px"
        min_width = "60px"
    else:  # normal
        padding = "10px 16px"
        font_size = "13px"
        min_width = "80px"

    # Get color properties based on button type
    if button_type == 'primary':
        bg_color = COLORS['primary']
        hover_color = COLORS['hover']
        text_color = "white"
    elif button_type == 'success':
        bg_color = COLORS['success']
        hover_color = COLORS['success_hover']
        text_color = "white"
    elif button_type == 'warning':
        bg_color = COLORS['warning']
        hover_color = COLORS['warning_hover']
        text_color = "white"
    elif button_type == 'danger':
        bg_color = COLORS['danger']
        hover_color = COLORS['danger_hover']
        text_color = "white"
    elif button_type == 'info':
        bg_color = COLORS['info']
        hover_color = COLORS['info_hover']
        text_color = "white"
    elif button_type == 'secondary':
        bg_color = COLORS['secondary']
        hover_color = "#5a6268"
        text_color = "white"
    else:
        bg_color = COLORS['primary']
        hover_color = COLORS['hover']
        text_color = "white"

    # Return a single CSS rule for QPushButton
    return f"""
        QPushButton {{
            border-radius: 6px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 500;
            border: none;
            min-width: {min_width};
            min-height: 20px;
            background-color: {bg_color};
            color: {text_color};
        }}

        QPushButton:hover {{
            background-color: {hover_color};
        }}

        QPushButton:pressed {{
            background-color: {bg_color};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['secondary']};
            color: #adb5bd;
        }}
    """


def get_groupbox_style(theme='default'):
    """Get group box style based on theme"""
    if theme == 'blue':
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
    elif theme == 'green':
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
    elif theme == 'purple':
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
    elif theme == 'red':
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


def get_status_style(status_type='info'):
    """Get status message style"""
    if status_type == 'success':
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
    elif status_type == 'warning':
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
    elif status_type == 'error':
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
                table.setHorizontalHeaderItem(i, QTableWidgetItem(f"{emoji} {current_text}"))

    # Professional styling
    table.setStyleSheet(f"""
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
    """)

    # Set default row height for better button display
    table.verticalHeader().setDefaultSectionSize(60)


def create_professional_button(text, button_type='primary', size='normal', icon=None):
    """Create a professional button with proper styling"""
    button = QPushButton(text)
    button.setStyleSheet(get_button_style(button_type, size))

    if icon:
        # If icon is provided, you can add it here
        pass

    return button


def create_professional_groupbox(title, theme='default'):
    """Create a professional group box with proper styling"""
    groupbox = QGroupBox(title)
    groupbox.setStyleSheet(get_groupbox_style(theme))
    return groupbox


def create_status_label(text, status_type='info'):
    """Create a professional status label"""
    label = QLabel(text)
    label.setStyleSheet(get_status_style(status_type))
    return label


# Professional Layout Patterns
def create_form_row(label_text, widget, tooltip=None):
    """Create a professional form row with label and widget"""
    from PyQt5.QtWidgets import QHBoxLayout

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
    from PyQt5.QtWidgets import QHBoxLayout

    layout = QHBoxLayout()
    layout.setSpacing(12)

    for button in buttons:
        layout.addWidget(button)

    layout.addStretch()
    return layout


# Development Guidelines for Future Features
"""
FUTURE DEVELOPMENT GUIDELINES:

1. Always import and use this theme module:
   from scripts.Utilities.ui_theme import apply_theme, create_professional_button, get_groupbox_style

2. Apply theme to all new dialogs:
   def __init__(self, parent=None):
       super().__init__(parent)
       apply_theme(self)  # Apply professional theme

3. Use professional components:
   - create_professional_button() for all buttons
   - create_professional_groupbox() for all group boxes
   - setup_professional_table() for all tables
   - create_status_label() for status messages

4. Follow consistent color coding:
   - Blue (#007bff): Primary actions, links, focus states
   - Green (#28a745): Success, positive actions
   - Orange (#fd7e14): Warnings, secondary actions
   - Red (#dc3545): Errors, danger actions
   - Gray (#6c757d): Secondary, disabled states

5. Maintain proper spacing and sizing:
   - Button minimum height: 35px for normal, 45px for large
   - Input field minimum height: 35px
   - Table row height: 60px minimum for buttons
   - Consistent margins: 20px for dialogs, 15px for sections

6. Use meaningful emojis in headers and labels for better UX

7. Always test on different screen sizes and ensure responsive behavior
"""