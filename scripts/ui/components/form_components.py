from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QDateEdit, QGroupBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QWidget, QFrame
)
from PyQt5.QtCore import QDate, Qt
from scripts.Utilities.ui_theme import create_professional_button


class FormField:
    """Represents a form field with label and input widget"""

    def __init__(self, label_text, widget, tooltip=None, required=False):
        self.label_text = label_text
        self.widget = widget
        self.tooltip = tooltip
        self.required = required
        self.label = None

    def get_value(self):
        """Get the current value of the field"""
        if hasattr(self.widget, 'text'):
            return self.widget.text().strip()
        elif hasattr(self.widget, 'toPlainText'):
            return self.widget.toPlainText().strip()
        elif hasattr(self.widget, 'currentText'):
            return self.widget.currentText()
        elif hasattr(self.widget, 'date'):
            return self.widget.date().toString("yyyy-MM-dd")
        elif hasattr(self.widget, 'isChecked'):
            return self.widget.isChecked()
        elif hasattr(self.widget, 'value'):
            return self.widget.value()
        return ""

    def set_value(self, value):
        """Set the value of the field"""
        if hasattr(self.widget, 'setText'):
            self.widget.setText(str(value))
        elif hasattr(self.widget, 'setPlainText'):
            self.widget.setPlainText(str(value))
        elif hasattr(self.widget, 'setCurrentText'):
            self.widget.setCurrentText(str(value))
        elif hasattr(self.widget, 'setDate') and value:
            self.widget.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))
        elif hasattr(self.widget, 'setChecked'):
            self.widget.setChecked(bool(value))
        elif hasattr(self.widget, 'setValue'):
            self.widget.setValue(float(value) if isinstance(value, (int, float)) else 0)

    def is_empty(self):
        """Check if the field is empty"""
        value = self.get_value()
        return not value or value == ""

    def validate(self):
        """Validate the field"""
        if self.required and self.is_empty():
            return f"{self.label_text} is required"
        return None


class FormBuilder:
    """Helper class to build forms with consistent styling"""

    def __init__(self):
        self.fields = {}
        self.layout = QFormLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

    def add_text_field(self, name, label, placeholder="", required=False, multiline=False):
        """Add a text input field"""
        if multiline:
            widget = QTextEdit()
            widget.setPlaceholderText(placeholder)
            widget.setMinimumHeight(60)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(placeholder)

        return self._add_field(name, label, widget, required)

    def add_combo_field(self, name, label, items=None, required=False):
        """Add a combo box field"""
        widget = QComboBox()
        if items:
            widget.addItems(items)

        return self._add_field(name, label, widget, required)

    def add_date_field(self, name, label, required=False):
        """Add a date input field"""
        widget = QDateEdit(QDate.currentDate())
        widget.setCalendarPopup(True)

        return self._add_field(name, label, widget, required)

    def add_numeric_field(self, name, label, min_val=0, max_val=999999, decimals=2, required=False):
        """Add a numeric input field"""
        if decimals > 0:
            widget = QDoubleSpinBox()
            widget.setDecimals(decimals)
        else:
            widget = QSpinBox()

        widget.setRange(min_val, max_val)
        widget.setValue(min_val)

        return self._add_field(name, label, widget, required)

    def add_checkbox_field(self, name, label, checked=False):
        """Add a checkbox field"""
        widget = QCheckBox(label)
        widget.setChecked(checked)

        field = FormField("", widget, required=False)
        self.fields[name] = field

        # For checkboxes, we don't add to layout here as they handle their own label
        return field

    def add_file_field(self, name, label, browse_callback=None):
        """Add a file selection field"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        widget = QLineEdit()
        widget.setReadOnly(True)
        layout.addWidget(widget)

        if browse_callback:
            browse_btn = create_professional_button("Browse", "secondary")
            browse_btn.clicked.connect(browse_callback)
            layout.addWidget(browse_btn)

        return self._add_field(name, label, container, False)

    def _add_field(self, name, label, widget, required):
        """Add a field to the form"""
        field = FormField(label, widget, required=required)
        self.fields[name] = field

        # Create label with required indicator
        display_label = f"{label}:" + (" *" if required else "")
        label_widget = QLabel(display_label)
        label_widget.setStyleSheet("font-weight: bold;")

        self.layout.addRow(label_widget, widget)
        field.label = label_widget

        return field

    def add_separator(self):
        """Add a visual separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addRow(separator)

    def get_layout(self):
        """Get the form layout"""
        return self.layout

    def get_field(self, name):
        """Get a field by name"""
        return self.fields.get(name)

    def get_value(self, name):
        """Get the value of a field"""
        field = self.get_field(name)
        return field.get_value() if field else None

    def set_value(self, name, value):
        """Set the value of a field"""
        field = self.get_field(name)
        if field:
            field.set_value(value)

    def validate_all(self):
        """Validate all required fields"""
        errors = []
        for name, field in self.fields.items():
            error = field.validate()
            if error:
                errors.append(error)
        return errors

    def populate_from_dict(self, data_dict):
        """Populate form fields from a dictionary"""
        for name, value in data_dict.items():
            if name in self.fields:
                self.fields[name].set_value(value)

    def to_dict(self):
        """Convert form data to dictionary"""
        result = {}
        for name, field in self.fields.items():
            result[name] = field.get_value()
        return result


class FormSection:
    """A section of a form with a title"""

    def __init__(self, title, theme="default"):
        self.group = QGroupBox(title)
        from scripts.Utilities.ui_theme import get_groupbox_style
        self.group.setStyleSheet(get_groupbox_style(theme))
        self.layout = QVBoxLayout(self.group)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.form_builder = FormBuilder()
        self.layout.addLayout(self.form_builder.get_layout())

    def get_widget(self):
        """Get the group box widget"""
        return self.group

    def get_form_builder(self):
        """Get the form builder for this section"""
        return self.form_builder