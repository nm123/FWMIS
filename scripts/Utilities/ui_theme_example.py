"""
FWMIS Professional UI Theme - Implementation Example

This file demonstrates how to apply the professional UI theme to any dialog in
the FWMIS application. Follow this pattern for consistent styling across all
dialogs.

EXAMPLE USAGE:
"""

from PyQt5.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QTableWidget,
                             QVBoxLayout)
from scripts.Utilities.ui_theme import (COLORS, apply_theme,
                                        create_professional_button,
                                        create_professional_groupbox,
                                        create_status_label,
                                        setup_professional_table)


class ExampleDialog(QDialog):
    """Example dialog showing how to use the professional UI theme"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Example - Professional UI Dialog")
        self.setFixedSize(800, 600)

        # Apply the professional theme
        apply_theme(self)

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface using professional theme components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        header_layout = QHBoxLayout()
        header_label = QLabel("📊 Professional Dialog Example")
        header_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {COLORS['dark']};
                margin-bottom: 5px;
            }}
        """
        )
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form section using professional groupbox
        form_group = create_professional_groupbox("📝 Form Section", "blue")
        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        # Form fields with professional styling
        name_label = QLabel("👤 Name:")
        name_label.setStyleSheet("font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        self.name_input.setMinimumHeight(35)

        email_label = QLabel("📧 Email:")
        email_label.setStyleSheet("font-weight: bold;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email...")
        self.email_input.setMinimumHeight(35)

        # Layout the form fields
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(email_label, 1, 0)
        form_layout.addWidget(self.email_input, 1, 1)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Table section
        table_group = create_professional_groupbox("📋 Data Table", "green")
        table_layout = QVBoxLayout()

        table_header = QLabel("📊 Sample Data:")
        table_header.setStyleSheet(
            f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {COLORS['dark']};
                margin-bottom: 5px;
            }}
        """
        )
        table_layout.addWidget(table_header)

        # Create professional table
        self.data_table = QTableWidget()
        setup_professional_table(
            self.data_table,
            headers=["🏷️ ID", "📝 Name", "💰 Amount", "📅 Date"],
            emojis=["🏷️", "📝", "💰", "📅"],
        )
        self.data_table.setColumnWidth(0, 80)
        self.data_table.setColumnWidth(1, 150)
        self.data_table.setColumnWidth(2, 100)
        self.data_table.setColumnWidth(3, 120)

        table_layout.addWidget(self.data_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Status section
        self.status_label = create_status_label("Ready to process data", "info")
        layout.addWidget(self.status_label)

        # Action buttons section
        actions_group = create_professional_groupbox("🎯 Actions", "red")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(15)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # Create professional buttons
        self.save_button = create_professional_button("💾 Save", "success", "normal")
        self.save_button.clicked.connect(self.save_data)

        self.cancel_button = create_professional_button(
            "❌ Cancel", "secondary", "normal"
        )
        self.cancel_button.clicked.connect(self.reject)

        self.help_button = create_professional_button("❓ Help", "info", "small")
        self.help_button.clicked.connect(self.show_help)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.help_button)

        actions_layout.addLayout(button_layout)
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

    def save_data(self):
        """Handle save action"""
        # Update status
        self.status_label = create_status_label(
            "✅ Data saved successfully!", "success"
        )
        # In a real implementation, you'd update the existing label

        QMessageBox.information(self, "Success", "Data saved successfully!")

    def show_help(self):
        """Show help information"""
        QMessageBox.information(
            self,
            "Help",
            "This is an example of the professional UI theme.\n\n"
            "• Use apply_theme() to apply the base theme\n"
            "• Use create_professional_button() for consistent buttons\n"
            "• Use create_professional_groupbox() for sections\n"
            "• Use setup_professional_table() for tables\n"
            "• Use create_status_label() for status messages",
        )


"""
FWMIS PROFESSIONAL UI THEME - IMPLEMENTATION GUIDE

To apply this theme across the entire FWMIS application:

1. IMPORT THE THEME MODULE in every dialog:
   from scripts.Utilities.ui_theme import (
       apply_theme, create_professional_button, create_professional_groupbox,
       setup_professional_table, create_status_label, get_button_style,
       get_groupbox_style, COLORS
   )

2. APPLY THEME in dialog __init__:
   def __init__(self, parent=None):
       super().__init__(parent)
       apply_theme(self)  # Apply professional theme
       self.setWindowTitle("🎯 Your Dialog Title")
       self.setFixedSize(width, height)

3. USE PROFESSIONAL COMPONENTS:

   Instead of:
   button = QPushButton("Save")
   button.setStyleSheet("...long inline styles...")

   Use:
   button = create_professional_button("💾 Save", "success", "normal")

   Instead of:
   groupbox = QGroupBox("Section")
   groupbox.setStyleSheet("...long inline styles...")

   Use:
   groupbox = create_professional_groupbox("📋 Section", "blue")

   Instead of:
   table = QTableWidget()
   # Manual styling...

   Use:
   table = QTableWidget()
   setup_professional_table(table, headers=["Col1", "Col2"], emojis=["📝", "💰"])

4. COLOR CODING CONVENTIONS:
   - Blue (#007bff): Primary actions, links, focus states
   - Green (#28a745): Success, positive actions, confirmations
   - Orange (#fd7e14): Warnings, secondary actions
   - Red (#dc3545): Errors, danger actions, critical sections
   - Gray (#6c757d): Secondary, disabled states, cancel actions
   - Purple (#6f42c1): Special sections, management actions

5. ICON CONVENTIONS:
   - 📊 Data/Analytics
   - 📁 Files/Folders
   - ⚙️ Settings/Configuration
   - 🎯 Actions/Targets
   - ✅ Success/Valid
   - ❌ Cancel/Error
   - 🔍 Search/Find
   - 💾 Save
   - 👥 People/Users
   - 📋 Lists/Tasks
   - 💰 Money/Finance
   - 📅 Dates/Calendar
   - 🏢 Organizations
   - 🔢 Numbers/IDs

6. LAYOUT STANDARDS:
   - Dialog margins: 20px
   - Section spacing: 15px
   - Button minimum height: 35px (normal), 45px (large)
   - Input field minimum height: 35px
   - Table row height: 60px minimum
   - Consistent padding: 8px-12px for inputs, 10px-16px for buttons

7. RESPONSIVE DESIGN:
   - Test on different screen sizes
   - Use minimum widths/heights appropriately
   - Ensure text doesn't get cut off
   - Consider high-DPI displays

8. ACCESSIBILITY:
   - Use meaningful emojis and icons
   - Ensure sufficient color contrast
   - Provide clear visual feedback
   - Use descriptive button text

APPLY THIS THEME TO EXISTING DIALOGS:

1. Add theme import
2. Replace inline styles with theme functions
3. Update button creation to use create_professional_button()
4. Update group boxes to use create_professional_groupbox()
5. Update tables to use setup_professional_table()
6. Update status messages to use create_status_label()
7. Test thoroughly for visual consistency

This ensures a cohesive, professional user experience across the entire FWMIS application!
"""
