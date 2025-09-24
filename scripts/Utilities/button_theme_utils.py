"""
Button theming utilities.
"""

from PyQt5.QtWidgets import QPushButton

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


def get_button_style(button_type="primary", size="normal"):
    """Get professional corporate button style based on type and size"""
    # Get size properties for corporate styling
    if size == "large":
        padding = "12px 24px"
        font_size = "15px"
        min_width = "140px"
        min_height = "44px"
    elif size == "small":
        padding = "6px 16px"
        font_size = "12px"
        min_width = "80px"
        min_height = "28px"
    else:  # normal
        padding = "8px 20px"
        font_size = "14px"
        min_width = "100px"
        min_height = "36px"

    # Get color properties based on button type
    if button_type == "primary":
        bg_color = COLORS["primary"]
        hover_color = COLORS["hover"]
        text_color = "white"
        border_color = COLORS["primary"]
    elif button_type == "success":
        bg_color = COLORS["success"]
        hover_color = COLORS["success_hover"]
        text_color = "white"
        border_color = COLORS["success"]
    elif button_type == "warning":
        bg_color = COLORS["warning"]
        hover_color = COLORS["warning_hover"]
        text_color = "white"
        border_color = COLORS["warning"]
    elif button_type == "danger":
        bg_color = COLORS["danger"]
        hover_color = COLORS["danger_hover"]
        text_color = "white"
        border_color = COLORS["danger"]
    elif button_type == "info":
        bg_color = COLORS["info"]
        hover_color = COLORS["info_hover"]
        text_color = "white"
        border_color = COLORS["info"]
    elif button_type == "secondary":
        bg_color = "transparent"
        hover_color = COLORS["surface"]
        text_color = COLORS["dark"]
        border_color = COLORS["border"]
    else:
        bg_color = COLORS["primary"]
        hover_color = COLORS["hover"]
        text_color = "white"
        border_color = COLORS["primary"]

    # Return professional corporate CSS styling
    return f"""
        QPushButton {{
            border-radius: 4px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 500;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            border: 1px solid {border_color};
            min-width: {min_width};
            min-height: {min_height};
            background-color: {bg_color};
            color: {text_color};
        }}

        QPushButton:hover {{
            background-color: {hover_color};
            border-color: {border_color};
        }}

        QPushButton:pressed {{
            background-color: {bg_color};
            border-color: {border_color};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['surface']};
            color: {COLORS['muted']};
            border-color: {COLORS['border']};
        }}
    """


def create_professional_button(text, button_type="primary", size="normal", icon=None):
    """Create a professional button with proper styling"""
    button = QPushButton(text)
    button.setStyleSheet(get_button_style(button_type, size))

    if icon:
        # If icon is provided, you can add it here
        pass

    return button
