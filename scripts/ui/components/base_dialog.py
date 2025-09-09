from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from scripts.Utilities.ui_theme import apply_theme, create_professional_button


class BaseDialog(QDialog):
    """Base dialog class with common functionality"""

    def __init__(self, title="", parent=None, width=800, height=600):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)

        # Apply professional theme
        apply_theme(self)

        # Initialize common attributes
        self.setup_ui()

    def setup_ui(self):
        """Setup the basic UI structure. Override in subclasses."""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

    def create_button_row(self, buttons_config):
        """
        Create a row of buttons with standard styling

        Args:
            buttons_config: List of tuples (text, button_type, callback, enabled)
        """
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        for text, button_type, callback, enabled in buttons_config:
            button = create_professional_button(text, button_type)
            button.clicked.connect(callback)
            button.setEnabled(enabled)
            button_layout.addWidget(button)

        button_layout.addStretch()
        return button_layout

    def create_action_buttons(self, save_callback=None, cancel_callback=None, delete_callback=None):
        """Create standard action buttons (Save, Delete, Cancel)"""
        buttons_config = []

        if save_callback:
            buttons_config.append(("Save Changes", "primary", save_callback, True))

        if delete_callback:
            buttons_config.append(("Delete", "danger", delete_callback, True))

        if cancel_callback:
            buttons_config.append(("Cancel", "secondary", cancel_callback, True))
        else:
            buttons_config.append(("Cancel", "secondary", self.reject, True))

        return self.create_button_row(buttons_config)

    def validate_required_fields(self, fields):
        """
        Validate that required fields are filled

        Args:
            fields: Dict of field_name: (widget, display_name)

        Returns:
            List of validation errors
        """
        errors = []

        for field_name, (widget, display_name) in fields.items():
            if hasattr(widget, 'text'):
                value = widget.text().strip()
            elif hasattr(widget, 'toPlainText'):
                value = widget.toPlainText().strip()
            elif hasattr(widget, 'currentText'):
                value = widget.currentText().strip()
            else:
                value = str(widget).strip()

            if not value:
                errors.append(f"{display_name} is required")

        return errors

    def show_validation_errors(self, errors):
        """Show validation errors to user"""
        from PyQt5.QtWidgets import QMessageBox

        if errors:
            error_text = "Please correct the following errors:\n\n" + "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Validation Error", error_text)
            return False
        return True

    def confirm_action(self, title, message, default_button="No"):
        """Show confirmation dialog"""
        from PyQt5.QtWidgets import QMessageBox

        buttons = QMessageBox.Yes | QMessageBox.No
        default = QMessageBox.No if default_button == "No" else QMessageBox.Yes

        reply = QMessageBox.question(self, title, message, buttons, default)
        return reply == QMessageBox.Yes

    def show_success_message(self, title, message):
        """Show success message"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    def show_error_message(self, title, message):
        """Show error message"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)

    def load_combo_box_data(self, combo_box, data_list, value_field='name', display_field='name'):
        """Load data into a combo box"""
        combo_box.clear()
        for item in data_list:
            if isinstance(item, dict):
                display_text = item.get(display_field, '')
                value = item.get(value_field, '')
            else:
                display_text = str(item)
                value = item

            combo_box.addItem(display_text, value)

    def get_combo_box_value(self, combo_box):
        """Get the selected value from a combo box"""
        return combo_box.itemData(combo_box.currentIndex())

    def set_combo_box_value(self, combo_box, value):
        """Set the selected value in a combo box"""
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == value:
                combo_box.setCurrentIndex(i)
                break