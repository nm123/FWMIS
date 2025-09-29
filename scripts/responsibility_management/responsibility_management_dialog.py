"""
Responsibility Management Dialog Module

Contains the main ResponsibilityManagementDialog class for managing responsibilities.
"""

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

# Import Qt components for use throughout the class
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTreeWidget, QTableWidgetItem


class ContactDialog:
    """
    Dialog for adding/editing contacts.
    """

    def __init__(self, parent=None, contact_data: Optional[Dict] = None):
        """
        Initialize the contact dialog.

        Args:
            parent: Parent widget
            contact_data: Existing contact data for editing, None for new contact
        """
        from PyQt5.QtWidgets import (
            QVBoxLayout, QFormLayout, QHBoxLayout,
            QLineEdit, QPushButton, QLabel
        )

        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Add Contact" if contact_data is None else "Edit Contact")
        self.dialog.resize(400, 300)

        self.contact_data = contact_data or {}
        self.is_editing = contact_data is not None

        # Create form layout
        layout = QVBoxLayout(self.dialog)

        form_layout = QFormLayout()

        # Title field
        self.title_edit = QLineEdit(self.contact_data.get("title", ""))
        form_layout.addRow("Title:", self.title_edit)

        # Initials field
        self.initials_edit = QLineEdit(self.contact_data.get("initials", ""))
        form_layout.addRow("Initials:", self.initials_edit)

        # Names field
        self.names_edit = QLineEdit(self.contact_data.get("names", ""))
        form_layout.addRow("Names:", self.names_edit)

        # Surname field
        self.surname_edit = QLineEdit(self.contact_data.get("surname", ""))
        form_layout.addRow("Surname:", self.surname_edit)

        # Job Title field
        self.job_title_edit = QLineEdit(self.contact_data.get("job_title", ""))
        form_layout.addRow("Job Title:", self.job_title_edit)

        # Telephone field
        self.telephone_edit = QLineEdit(self.contact_data.get("telephone", ""))
        form_layout.addRow("Telephone:", self.telephone_edit)

        # Email field
        self.email_edit = QLineEdit(self.contact_data.get("email", ""))
        form_layout.addRow("Email:", self.email_edit)

        layout.addLayout(form_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._accept)
        buttons_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.dialog.reject)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

        # Set tab order
        self.title_edit.setFocus()

    def _accept(self):
        """Validate and accept the dialog."""
        # Basic validation - at least names and surname should be filled
        if not self.names_edit.text().strip() or not self.surname_edit.text().strip():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "Validation Error",
                "Names and Surname are required fields."
            )
            return

        self.contact_data = {
            "title": self.title_edit.text().strip(),
            "initials": self.initials_edit.text().strip(),
            "names": self.names_edit.text().strip(),
            "surname": self.surname_edit.text().strip(),
            "job_title": self.job_title_edit.text().strip(),
            "telephone": self.telephone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
        }

        self.dialog.accept()

    def get_contact_data(self) -> Dict:
        """Get the contact data from the form."""
        return self.contact_data

    def show(self) -> int:
        """Show the dialog and return the result."""
        return self.dialog.exec_()


class ResponsibilityManagementDialog:
    """
    Main dialog for managing responsibilities hierarchy and contacts.
    """

    def __init__(self, parent=None):
        """
        Initialize the responsibility management dialog.

        Args:
            parent: Parent widget
        """
        from PyQt5.QtWidgets import QDialog

        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Responsibility Management")
        self.dialog.resize(1200, 800)

        self.responsibilities = []
        self.contacts = []
        self.selected_responsibility_id = None

        self._setup_ui()
        self._load_responsibilities()

    def _setup_ui(self) -> None:
        """Set up the dialog UI with horizontal layout (tree left, details right)."""
        from PyQt5.QtWidgets import (
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QSplitter,
            QTableWidget,
            QVBoxLayout,
        )
        # Qt components are imported at the top of the file

        main_layout = QHBoxLayout(self.dialog)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Responsibilities Tree
        left_widget = self._create_tree_panel()
        splitter.addWidget(left_widget)

        # Right panel - Details/Editing
        right_widget = self._create_details_panel()
        splitter.addWidget(right_widget)

        # Set splitter proportions (tree gets more space)
        splitter.setSizes([400, 800])

    def _create_tree_panel(self):
        """Create the left panel with responsibility tree."""
        from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tree section
        tree_group = QGroupBox("Responsibilities Hierarchy")
        tree_layout = QVBoxLayout(tree_group)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Responsibilities")
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        tree_layout.addWidget(self.tree)

        # Tree buttons
        tree_buttons_layout = QHBoxLayout()

        add_child_btn = QPushButton("Add Child")
        add_child_btn.clicked.connect(self._add_child_responsibility)
        tree_buttons_layout.addWidget(add_child_btn)

        add_root_btn = QPushButton("Add Root")
        add_root_btn.clicked.connect(self._add_root_responsibility)
        tree_buttons_layout.addWidget(add_root_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_responsibility)
        tree_buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_responsibility)
        tree_buttons_layout.addWidget(delete_btn)

        tree_buttons_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_responsibilities)
        tree_buttons_layout.addWidget(refresh_btn)

        tree_layout.addLayout(tree_buttons_layout)
        layout.addWidget(tree_group)

        return panel

    def _create_details_panel(self):
        """Create the right panel with responsibility details and editing."""
        from PyQt5.QtWidgets import (
            QCheckBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QTableWidget,
            QVBoxLayout,
            QWidget,
        )

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Responsibility Details section
        details_group = QGroupBox("Responsibility Details")
        details_layout = QFormLayout(details_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Responsibility name")
        details_layout.addRow("Name:", self.name_edit)

        self.posting_checkbox = QCheckBox("Posting Level Responsibility")
        self.posting_checkbox.setToolTip("Check if this responsibility can have cases assigned to it")
        details_layout.addRow("", self.posting_checkbox)

        # Buttons for editing
        edit_buttons_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._save_responsibility_changes)
        self.save_btn.setEnabled(False)
        edit_buttons_layout.addWidget(self.save_btn)

        self.cancel_edit_btn = QPushButton("Cancel")
        self.cancel_edit_btn.clicked.connect(self._cancel_edit)
        self.cancel_edit_btn.setEnabled(False)
        edit_buttons_layout.addWidget(self.cancel_edit_btn)

        details_layout.addRow(edit_buttons_layout)

        layout.addWidget(details_group)

        # Contacts section
        contacts_group = QGroupBox("Contacts")
        contacts_layout = QVBoxLayout(contacts_group)

        # Contacts table
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(7)
        self.contacts_table.setHorizontalHeaderLabels(["Title", "Initials", "Names", "Surname", "Job Title", "Telephone", "Email"])
        contacts_layout.addWidget(self.contacts_table)

        # Contact buttons
        contact_buttons_layout = QHBoxLayout()

        add_contact_btn = QPushButton("Add Contact")
        add_contact_btn.clicked.connect(self._add_contact)
        contact_buttons_layout.addWidget(add_contact_btn)

        edit_contact_btn = QPushButton("Edit Contact")
        edit_contact_btn.clicked.connect(self._edit_contact)
        contact_buttons_layout.addWidget(edit_contact_btn)

        delete_contact_btn = QPushButton("Delete Contact")
        delete_contact_btn.clicked.connect(self._delete_contact)
        contact_buttons_layout.addWidget(delete_contact_btn)

        copy_from_parent_btn = QPushButton("Copy from Parent")
        copy_from_parent_btn.clicked.connect(self._copy_contacts_from_parent)
        copy_from_parent_btn.setToolTip("Copy all contacts from the parent responsibility")
        contact_buttons_layout.addWidget(copy_from_parent_btn)

        contact_buttons_layout.addStretch()

        contacts_layout.addLayout(contact_buttons_layout)
        layout.addWidget(contacts_group)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.dialog.reject)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

        return panel

    def _load_responsibilities(self):
        """Load responsibilities and build the tree."""
        try:
            import sqlite3
            try:
                from scripts.Utilities.config import DB_PATH
            except ImportError:
                # Fallback to hardcoded path
                import os
                DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fruitless.db')

            try:
                from scripts.Utilities.responsibility_tree_utils import build_responsibility_tree
            except ImportError:
                # Try alternative import path
                try:
                    import sys
                    import os
                    # Add scripts directory to path
                    scripts_dir = os.path.dirname(os.path.dirname(__file__))
                    if scripts_dir not in sys.path:
                        sys.path.insert(0, scripts_dir)
                    from Utilities.responsibility_tree_utils import build_responsibility_tree
                except ImportError:
                    # Fallback: define a proper hierarchical tree builder
                    from collections import defaultdict
                    def build_responsibility_tree(tree_widget, responsibilities, show_posting_only=False, highlight_ids=None):
                        tree_widget.clear()

                        # Filter responsibilities if needed
                        if show_posting_only:
                            filtered_resp = [r for r in responsibilities if r.get("is_posting_level", 0)]
                        else:
                            filtered_resp = responsibilities

                        # Create parent map
                        parent_map = defaultdict(list)
                        for resp in filtered_resp:
                            parent_map[resp["parent_id"]].append(resp)

                        def add_tree_item(resp, parent_item=None):
                            """Recursively add responsibility to tree"""
                            from PyQt5.QtWidgets import QTreeWidgetItem
                            from PyQt5.QtGui import QFont

                            item = QTreeWidgetItem([resp["name"]])
                            item.setData(0, 0, resp["id"])  # Qt.UserRole

                            # Style posting level items
                            if resp.get("is_posting_level", 0):
                                font = item.font(0)
                                font.setBold(True)
                                item.setFont(0, font)

                            # Add to tree
                            if parent_item is None:
                                tree_widget.addTopLevelItem(item)
                            else:
                                parent_item.addChild(item)

                            # Add children recursively
                            children = sorted(parent_map[resp["id"]], key=lambda x: (x.get("sort_order", 999), x["name"]))
                            for child in children:
                                add_tree_item(child, item)

                        # Add top-level items (no parent)
                        top_level = sorted(parent_map[None], key=lambda x: (x.get("sort_order", 999), x["name"]))
                        for resp in top_level:
                            add_tree_item(resp)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Load all responsibilities
            cursor.execute(
                "SELECT id, name, parent_id, is_posting_level, sort_order FROM responsibilities ORDER BY name"
            )
            self.responsibilities = [
                {
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "is_posting_level": row[3],
                    "sort_order": row[4],
                }
                for row in cursor.fetchall()
            ]

            # Load contacts
            cursor.execute(
                """
                SELECT c.id, c.name, c.email, c.telephone, c.responsibility_id
                FROM contacts c
                ORDER BY c.name
                """
            )
            self.contacts = [
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "telephone": row[3],
                    "responsibility_id": row[4],
                }
                for row in cursor.fetchall()
            ]

            conn.close()

            # Build the responsibility tree
            build_responsibility_tree(self.tree, self.responsibilities)

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.dialog, "Error", f"Failed to load responsibilities: {str(e)}"
            )

    def _save_tree_expanded_state(self):
        """Save the current expanded state of tree items."""
        self._expanded_item_ids = set()

        def collect_expanded_items(item):
            if item.isExpanded():
                # Get responsibility ID from the item
                resp_id = item.data(0, 0)  # Qt.UserRole
                if resp_id:
                    self._expanded_item_ids.add(resp_id)

            # Recursively check children
            for i in range(item.childCount()):
                collect_expanded_items(item.child(i))

        # Start from root items
        for i in range(self.tree.topLevelItemCount()):
            collect_expanded_items(self.tree.topLevelItem(i))

    def _restore_tree_expanded_state(self):
        """Restore the expanded state of tree items."""
        if not hasattr(self, '_expanded_item_ids'):
            return

        def expand_items(item):
            # Get responsibility ID from the item
            resp_id = item.data(0, 0)  # Qt.UserRole
            if resp_id in self._expanded_item_ids:
                item.setExpanded(True)

            # Recursively expand children
            for i in range(item.childCount()):
                expand_items(item.child(i))

        # Start from root items
        for i in range(self.tree.topLevelItemCount()):
            expand_items(self.tree.topLevelItem(i))

    def _load_responsibilities_preserve_tree_state(self):
        """Load responsibilities while preserving tree expansion state."""
        # Save current expanded state
        self._save_tree_expanded_state()

        # Load responsibilities
        self._load_responsibilities()

        # Restore expanded state
        self._restore_tree_expanded_state()

    def _on_tree_selection_changed(self):
        """Handle tree selection changes."""
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.selected_responsibility_id = item.data(0, Qt.UserRole)

            # Load responsibility details
            self._load_responsibility_details(self.selected_responsibility_id)

            # Load contacts for this responsibility
            self._load_contacts_for_responsibility(self.selected_responsibility_id)
        else:
            self.selected_responsibility_id = None
            self._clear_details()

    def _load_responsibility_details(self, resp_id):
        """Load details for the selected responsibility."""
        resp = next((r for r in self.responsibilities if r["id"] == resp_id), None)
        if resp:
            self.name_edit.setText(resp["name"])
            self.posting_checkbox.setChecked(resp["is_posting_level"] == 1)

            # Disable editing by default (enable when editing)
            self.name_edit.setReadOnly(True)
            self.posting_checkbox.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.cancel_edit_btn.setEnabled(False)

    def _load_contacts_for_responsibility(self, resp_id):
        """Load contacts for the selected responsibility."""
        # Filter contacts for this responsibility
        resp_contacts = [c for c in self.contacts if c["responsibility_id"] == resp_id]

        # Update contacts table
        self.contacts_table.setRowCount(len(resp_contacts))
        for row, contact in enumerate(resp_contacts):
            from PyQt5.QtWidgets import QTableWidgetItem

            # Title
            title_item = QTableWidgetItem(contact.get("title", ""))
            self.contacts_table.setItem(row, 0, title_item)

            # Initials
            initials_item = QTableWidgetItem(contact.get("initials", ""))
            self.contacts_table.setItem(row, 1, initials_item)

            # Names
            names_item = QTableWidgetItem(contact.get("names", ""))
            self.contacts_table.setItem(row, 2, names_item)

            # Surname
            surname_item = QTableWidgetItem(contact.get("surname", ""))
            self.contacts_table.setItem(row, 3, surname_item)

            # Job Title
            job_title_item = QTableWidgetItem(contact.get("job_title", ""))
            self.contacts_table.setItem(row, 4, job_title_item)

            # Telephone
            telephone_item = QTableWidgetItem(contact.get("telephone", ""))
            self.contacts_table.setItem(row, 5, telephone_item)

            # Email
            email_item = QTableWidgetItem(contact.get("email", ""))
            self.contacts_table.setItem(row, 6, email_item)

    def _clear_details(self):
        """Clear the details panel."""
        self.name_edit.clear()
        self.posting_checkbox.setChecked(False)
        self.contacts_table.setRowCount(0)

    def _add_root_responsibility(self):
        """Add a new root-level responsibility."""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        name, ok = QInputDialog.getText(
            self.dialog, "Add Root Responsibility",
            "Enter responsibility name:"
        )

        if ok and name.strip():
            try:
                import sqlite3
                from scripts.Utilities.config import DB_PATH

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    "INSERT INTO responsibilities (name, parent_id, is_posting_level) VALUES (?, ?, ?)",
                    (name.strip(), None, 0)
                )

                conn.commit()
                conn.close()

                QMessageBox.information(
                    self.dialog, "Success", "Root responsibility added successfully."
                )

                self._load_responsibilities_preserve_tree_state()

            except Exception as e:
                QMessageBox.critical(
                    self.dialog, "Error", f"Failed to add responsibility: {str(e)}"
                )

    def _add_child_responsibility(self):
        """Add a child responsibility to the selected responsibility."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a parent responsibility first."
            )
            return

        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        name, ok = QInputDialog.getText(
            self.dialog, "Add Child Responsibility",
            "Enter responsibility name:"
        )

        if ok and name.strip():
            try:
                import sqlite3
                from scripts.Utilities.config import DB_PATH

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    "INSERT INTO responsibilities (name, parent_id, is_posting_level) VALUES (?, ?, ?)",
                    (name.strip(), self.selected_responsibility_id, 0)
                )

                conn.commit()
                conn.close()

                QMessageBox.information(
                    self.dialog, "Success", "Child responsibility added successfully."
                )

                self._load_responsibilities_preserve_tree_state()

            except Exception as e:
                QMessageBox.critical(
                    self.dialog, "Error", f"Failed to add responsibility: {str(e)}"
                )

    def _edit_responsibility(self):
        """Enable editing of the selected responsibility."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility to edit."
            )
            return

        # Enable editing controls
        self.name_edit.setReadOnly(False)
        self.posting_checkbox.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_edit_btn.setEnabled(True)

    def _save_responsibility_changes(self):
        """Save changes to the selected responsibility."""
        if not self.selected_responsibility_id:
            return

        name = self.name_edit.text().strip()
        is_posting = 1 if self.posting_checkbox.isChecked() else 0

        if not name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "Invalid Input", "Responsibility name cannot be empty."
            )
            return

        try:
            import sqlite3
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE responsibilities SET name = ?, is_posting_level = ? WHERE id = ?",
                (name, is_posting, self.selected_responsibility_id)
            )

            conn.commit()
            conn.close()

            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self.dialog, "Success", "Responsibility updated successfully."
            )

            # Disable editing controls
            self.name_edit.setReadOnly(True)
            self.posting_checkbox.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.cancel_edit_btn.setEnabled(False)

            # Preserve tree expansion state before reloading
            self._load_responsibilities_preserve_tree_state()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.dialog, "Error", f"Failed to save changes: {str(e)}"
            )

    def _cancel_edit(self):
        """Cancel editing and reload original data."""
        if self.selected_responsibility_id:
            self._load_responsibility_details(self.selected_responsibility_id)

        # Disable editing controls
        self.name_edit.setReadOnly(True)
        self.posting_checkbox.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_edit_btn.setEnabled(False)

    def _delete_responsibility(self):
        """Delete the selected responsibility."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility to delete."
            )
            return

        # Check if responsibility has children
        children = [r for r in self.responsibilities if r["parent_id"] == self.selected_responsibility_id]
        has_cases = False  # TODO: Check if responsibility has cases

        warning_msg = "Are you sure you want to delete this responsibility?"
        if children:
            warning_msg += f"\n\nWarning: This responsibility has {len(children)} child responsibilities that will also be deleted."
        if has_cases:
            warning_msg += "\n\nWarning: This responsibility has cases assigned to it."

        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.dialog, "Confirm Delete", warning_msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                import sqlite3
                from scripts.Utilities.config import DB_PATH

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Delete the responsibility (cascade will handle children and contacts)
                cursor.execute("DELETE FROM responsibilities WHERE id = ?", (self.selected_responsibility_id,))

                conn.commit()
                conn.close()

                QMessageBox.information(
                    self.dialog, "Success", "Responsibility deleted successfully."
                )

                self._load_responsibilities_preserve_tree_state()
                self._clear_details()

            except Exception as e:
                QMessageBox.critical(
                    self.dialog, "Error", f"Failed to delete responsibility: {str(e)}"
                )

    def _add_contact(self):
        """Add a new contact for the selected responsibility."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility first."
            )
            return

        # Open contact dialog
        contact_dialog = ContactDialog(self.dialog)
        result = contact_dialog.show()
        if result == QDialog.Accepted:
            contact_data = contact_dialog.get_contact_data()

            try:
                import sqlite3
                from scripts.Utilities.config import DB_PATH

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO contacts (
                        responsibility_id, title, initials, names, surname,
                        job_title, telephone, email
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.selected_responsibility_id,
                        contact_data.get("title", ""),
                        contact_data.get("initials", ""),
                        contact_data.get("names", ""),
                        contact_data.get("surname", ""),
                        contact_data.get("job_title", ""),
                        contact_data.get("telephone", ""),
                        contact_data.get("email", ""),
                    ),
                )

                conn.commit()
                conn.close()

                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.dialog, "Success", "Contact added successfully."
                )

                # Reload to show the new contact
                self._load_responsibilities_preserve_tree_state()

            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self.dialog, "Database Error", f"Failed to add contact: {str(e)}"
                )

    def _edit_contact(self):
        """Edit the selected contact."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility first."
            )
            return

        # Get selected row from contacts table
        selected_rows = set()
        for item in self.contacts_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a contact to edit."
            )
            return

        if len(selected_rows) > 1:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "Multiple Selection", "Please select only one contact to edit."
            )
            return

        row = list(selected_rows)[0]

        # Get existing contact data from the table
        existing_contact = {
            "title": self.contacts_table.item(row, 0).text() if self.contacts_table.item(row, 0) else "",
            "initials": self.contacts_table.item(row, 1).text() if self.contacts_table.item(row, 1) else "",
            "names": self.contacts_table.item(row, 2).text() if self.contacts_table.item(row, 2) else "",
            "surname": self.contacts_table.item(row, 3).text() if self.contacts_table.item(row, 3) else "",
            "job_title": self.contacts_table.item(row, 4).text() if self.contacts_table.item(row, 4) else "",
            "telephone": self.contacts_table.item(row, 5).text() if self.contacts_table.item(row, 5) else "",
            "email": self.contacts_table.item(row, 6).text() if self.contacts_table.item(row, 6) else "",
        }

        # Find the contact ID from the loaded contacts data
        resp_contacts = [c for c in self.contacts if c["responsibility_id"] == self.selected_responsibility_id]
        if row >= len(resp_contacts):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.dialog, "Error", "Contact data mismatch."
            )
            return

        contact_id = resp_contacts[row]["id"]

        # Open contact dialog with existing data
        contact_dialog = ContactDialog(self.dialog, existing_contact)
        result = contact_dialog.show()
        if result == QDialog.Accepted:
            contact_data = contact_dialog.get_contact_data()

            try:
                import sqlite3
                from scripts.Utilities.config import DB_PATH

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE contacts SET
                        title = ?, initials = ?, names = ?, surname = ?,
                        job_title = ?, telephone = ?, email = ?
                    WHERE id = ?
                    """,
                    (
                        contact_data.get("title", ""),
                        contact_data.get("initials", ""),
                        contact_data.get("names", ""),
                        contact_data.get("surname", ""),
                        contact_data.get("job_title", ""),
                        contact_data.get("telephone", ""),
                        contact_data.get("email", ""),
                        contact_id,
                    ),
                )

                conn.commit()
                conn.close()

                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.dialog, "Success", "Contact updated successfully."
                )

                # Reload to show the updated contact
                self._load_responsibilities_preserve_tree_state()

            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self.dialog, "Database Error", f"Failed to update contact: {str(e)}"
                )

    def _delete_contact(self):
        """Delete the selected contact."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility first."
            )
            return

        # Get selected rows from contacts table
        selected_rows = set()
        for item in self.contacts_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a contact to delete."
            )
            return

        # Confirm deletion
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.dialog, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_rows)} contact(s)?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            import sqlite3
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Find the contact IDs from the loaded contacts data
            resp_contacts = [c for c in self.contacts if c["responsibility_id"] == self.selected_responsibility_id]
            contact_ids_to_delete = []

            for row in selected_rows:
                if row < len(resp_contacts):
                    contact_ids_to_delete.append(resp_contacts[row]["id"])

            if contact_ids_to_delete:
                # Delete the selected contacts
                placeholders = ",".join("?" * len(contact_ids_to_delete))
                cursor.execute(
                    f"DELETE FROM contacts WHERE id IN ({placeholders})",
                    contact_ids_to_delete
                )

                conn.commit()

                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.dialog, "Success",
                    f"Successfully deleted {len(contact_ids_to_delete)} contact(s)."
                )

                # Reload to show the updated contacts
                self._load_responsibilities_preserve_tree_state()
            else:
                QMessageBox.warning(
                    self.dialog, "Error", "Could not identify contacts to delete."
                )

            conn.close()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.dialog, "Database Error", f"Failed to delete contacts: {str(e)}"
            )

    def _copy_contacts_from_parent(self):
        """Copy all contacts from the parent responsibility."""
        if not self.selected_responsibility_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Selection", "Please select a responsibility first."
            )
            return

        # Find the parent responsibility
        selected_resp = next((r for r in self.responsibilities if r["id"] == self.selected_responsibility_id), None)
        if not selected_resp or not selected_resp["parent_id"]:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.dialog, "No Parent", "This responsibility has no parent to copy contacts from."
            )
            return

        parent_id = selected_resp["parent_id"]
        parent_contacts = [c for c in self.contacts if c["responsibility_id"] == parent_id]

        if not parent_contacts:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self.dialog, "No Contacts", "The parent responsibility has no contacts to copy."
            )
            return

        try:
            import sqlite3
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Insert parent contacts for this responsibility
            for contact in parent_contacts:
                cursor.execute(
                    """
                    INSERT INTO contacts (
                        responsibility_id, name, email, telephone, title, initials,
                        names, surname, job_title
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.selected_responsibility_id,
                        contact.get("name", ""),
                        contact.get("email", ""),
                        contact.get("telephone", ""),
                        contact.get("title", ""),
                        contact.get("initials", ""),
                        contact.get("names", ""),
                        contact.get("surname", ""),
                        contact.get("job_title", ""),
                    ),
                )

            conn.commit()
            conn.close()

            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self.dialog, "Success",
                f"Successfully copied {len(parent_contacts)} contacts from parent responsibility."
            )

            # Reload to show the new contacts
            self._load_responsibilities_preserve_tree_state()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.dialog, "Database Error", f"Failed to copy contacts: {str(e)}"
            )

    def show(self):
        """Show the dialog."""
        return self.dialog.exec_()
        """Add a child responsibility to the selected item."""
