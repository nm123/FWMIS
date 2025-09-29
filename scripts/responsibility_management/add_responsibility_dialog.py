"""
Add Responsibility Dialog Module

Contains the AddResponsibilityDialog class for adding new responsibilities.
"""

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class AddResponsibilityDialog:
    """
    Dialog for adding new responsibilities with contact management.
    """

    def __init__(
        self, parent=None, parent_id=None, parent_name=None, inherited_contacts=None
    ):
        """
        Initialize the add responsibility dialog.

        Args:
            parent: Parent widget
            parent_id: ID of parent responsibility
            parent_name: Name of parent responsibility
            inherited_contacts: Contacts inherited from parent
        """
        from PyQt5.QtWidgets import QDialog

        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Add Child Responsibility")
        self.dialog.resize(750, 500)

        self.parent_id = parent_id
        self.parent_name = parent_name or "None"
        self.inherited_contacts = inherited_contacts or []

        self._setup_ui()
        self._load_inherited_contacts()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        from PyQt5.QtWidgets import (
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QRadioButton,
            QVBoxLayout,
        )

        layout = QVBoxLayout(self.dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Form for responsibility details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Parent label (non-editable)
        self.parent_label = QLineEdit(self.dialog)
        self.parent_label.setText(self.parent_name)
        self.parent_label.setReadOnly(True)
        self.parent_label.setToolTip(
            "Parent responsibility (selected from main dialog)"
        )
        form_layout.addRow("Parent:", self.parent_label)

        # Name input
        self.name_edit = QLineEdit(self.dialog)
        self.name_edit.setToolTip(
            "Enter a unique responsibility name, max 100 characters"
        )
        form_layout.addRow("Name:", self.name_edit)

        # Posting level radio buttons
        posting_group = QGroupBox("Posting Level")
        posting_layout = QHBoxLayout()
        self.posting_yes = QRadioButton("Posting Level")
        self.posting_no = QRadioButton("Non-Posting Level")
        self.posting_no.setChecked(True)
        posting_layout.addWidget(self.posting_yes)
        posting_layout.addWidget(self.posting_no)
        posting_group.setLayout(posting_layout)
        form_layout.addRow(posting_group)

        layout.addLayout(form_layout)

        # Contacts table
        contacts_group = QGroupBox("Contacts")
        contacts_layout = QVBoxLayout()

        from PyQt5.QtWidgets import QTableWidget

        self.contacts_table = QTableWidget(self.dialog)

        from .ui_components import UIComponents

        UIComponents.setup_contacts_table(self.contacts_table)

        contacts_layout.addWidget(self.contacts_table)
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        add_contact_btn = QPushButton("Add Contact")
        add_contact_btn.clicked.connect(self._add_contact)
        buttons_layout.addWidget(add_contact_btn)

        remove_contact_btn = QPushButton("Remove Contact")
        remove_contact_btn.clicked.connect(self._remove_contact)
        buttons_layout.addWidget(remove_contact_btn)

        buttons_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_responsibility)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def _load_inherited_contacts(self) -> None:
        """Load inherited contacts from parent responsibility."""
        from .ui_components import UIComponents

        UIComponents.populate_contacts_table(
            self.contacts_table, self.inherited_contacts
        )

    def _add_contact(self) -> None:
        """Add a new contact row to the table."""
        from PyQt5.QtWidgets import QTableWidgetItem

        row_count = self.contacts_table.rowCount()
        self.contacts_table.insertRow(row_count)

        # Add empty items for each column
        for col in range(7):
            self.contacts_table.setItem(row_count, col, QTableWidgetItem(""))

    def _remove_contact(self) -> None:
        """Remove the selected contact row from the table."""
        current_row = self.contacts_table.currentRow()
        if current_row >= 0:
            self.contacts_table.removeRow(current_row)

    def _save_responsibility(self) -> None:
        """Save the new responsibility."""
        from .ui_components import UIComponents

        # Get form data
        name = self.name_edit.text().strip()
        is_posting_level = self.posting_yes.isChecked()

        # Get contacts from table
        contacts = UIComponents.get_contacts_from_table(self.contacts_table)

        # Prepare data for saving
        data = {
            "name": name,
            "parent_id": self.parent_id,
            "is_posting_level": is_posting_level,
            "contacts": contacts,
            "inherited_contacts": self.inherited_contacts,
        }

        # Save using the operations module
        from .responsibility_management import add_responsibility

        if add_responsibility(self.dialog, data):
            self.dialog.accept()

    def exec_(self):
        """Execute the dialog."""
        return self.dialog.exec_()
