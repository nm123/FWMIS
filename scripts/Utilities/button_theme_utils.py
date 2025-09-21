"""
Button theming utilities.
"""

from PyQt5.QtWidgets import QPushButton

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


def create_professional_button(text, button_type='primary', size='normal', icon=None):
    """Create a professional button with proper styling"""
    button = QPushButton(text)
    button.setStyleSheet(get_button_style(button_type, size))

    if icon:
        # If icon is provided, you can add it here
        pass

    return button