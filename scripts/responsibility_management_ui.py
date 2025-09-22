import os
import re
import sqlite3
from collections import defaultdict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QRadioButton, QTableWidget,
                             QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout)
from scripts.responsibility_management_actions import (add_responsibility,
                                                       delete_responsibility,
                                                       edit_responsibility)
from scripts.Utilities.config import BASE_DIR, DB_PATH
from scripts.Utilities.validation_utils import is_valid_email


class AddResponsibilityDialog(QDialog):
    def __init__(
        self, parent=None, parent_id=None, parent_name=None, inherited_contacts=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Add Child Responsibility")
        self.resize(750, 500)  # Increased width by 25% for easier email capture
        self.parent_id = parent_id
        self.parent_name = parent_name or "None"
        self.inherited_contacts = inherited_contacts or []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Form for responsibility details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Parent label (non-editable)
        self.parent_label = QLineEdit(self)
        self.parent_label.setText(self.parent_name)
        self.parent_label.setReadOnly(True)
        self.parent_label.setToolTip(
            "Parent responsibility (selected from main dialog)"
        )
        form_layout.addRow("Parent:", self.parent_label)

        # Name input
        self.name_edit = QLineEdit(self)
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
        self.contacts_table = QTableWidget(self)
        self.contacts_table.setColumnCount(7)
        self.contacts_table.setHorizontalHeaderLabels(
            ["Title", "Initials", "Names", "Surname", "Job Title", "Telephone", "Email"]
        )
        header = self.contacts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.contacts_table.setColumnWidth(0, 80)  # Title
        self.contacts_table.setColumnWidth(1, 80)  # Initials
        self.contacts_table.setColumnWidth(2, 120)  # Names
        self.contacts_table.setColumnWidth(3, 120)  # Surname
        self.contacts_table.setColumnWidth(4, 120)  # Job Title
        self.contacts_table.setColumnWidth(5, 120)  # Telephone
        self.contacts_table.setColumnWidth(6, 200)  # Email
        self.contacts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.setEditTriggers(
            QTableWidget.AllEditTriggers
        )  # Enable editing on any trigger
        self.contacts_table.setToolTip(
            "Click on cells to edit contacts. Use Add/Remove buttons or double-click to edit."
        )
        contacts_layout.addWidget(self.contacts_table)
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copy from Parent")
        self.copy_button.clicked.connect(self.copy_from_parent)
        self.add_contact_button = QPushButton("Add Contact")
        self.add_contact_button.clicked.connect(self.add_contact_row)
        self.remove_contact_button = QPushButton("Remove Contact")
        self.remove_contact_button.clicked.connect(self.remove_contact_row)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.add_contact_button)
        button_layout.addWidget(self.remove_contact_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Populate inherited contacts
        for contact in self.inherited_contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)
            self.contacts_table.setItem(
                row, 0, QTableWidgetItem(contact.get("title", ""))
            )
            self.contacts_table.setItem(
                row, 1, QTableWidgetItem(contact.get("initials", ""))
            )
            self.contacts_table.setItem(
                row, 2, QTableWidgetItem(contact.get("names", contact.get("name", "")))
            )
            self.contacts_table.setItem(
                row, 3, QTableWidgetItem(contact.get("surname", ""))
            )
            self.contacts_table.setItem(
                row, 4, QTableWidgetItem(contact.get("job_title", ""))
            )
            self.contacts_table.setItem(
                row, 5, QTableWidgetItem(contact.get("telephone", ""))
            )
            self.contacts_table.setItem(
                row, 6, QTableWidgetItem(contact.get("email", ""))
            )

    def copy_from_parent(self):
        # Clear existing contacts first
        self.contacts_table.setRowCount(0)
        # Then copy from parent
        for contact in self.inherited_contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)
            self.contacts_table.setItem(
                row, 0, QTableWidgetItem(contact.get("title", ""))
            )
            self.contacts_table.setItem(
                row, 1, QTableWidgetItem(contact.get("initials", ""))
            )
            self.contacts_table.setItem(
                row, 2, QTableWidgetItem(contact.get("names", contact.get("name", "")))
            )
            self.contacts_table.setItem(
                row, 3, QTableWidgetItem(contact.get("surname", ""))
            )
            self.contacts_table.setItem(
                row, 4, QTableWidgetItem(contact.get("job_title", ""))
            )
            self.contacts_table.setItem(
                row, 5, QTableWidgetItem(contact.get("telephone", ""))
            )
            self.contacts_table.setItem(
                row, 6, QTableWidgetItem(contact.get("email", ""))
            )

    def add_contact_row(self):
        row = self.contacts_table.rowCount()
        self.contacts_table.insertRow(row)

    def remove_contact_row(self):
        selected = self.contacts_table.selectedItems()
        if selected:
            row = self.contacts_table.row(selected[0])
            self.contacts_table.removeRow(row)

    def get_data(self):
        contacts = []
        for row in range(self.contacts_table.rowCount()):
            title_item = self.contacts_table.item(row, 0)
            initials_item = self.contacts_table.item(row, 1)
            names_item = self.contacts_table.item(row, 2)
            surname_item = self.contacts_table.item(row, 3)
            job_title_item = self.contacts_table.item(row, 4)
            telephone_item = self.contacts_table.item(row, 5)
            email_item = self.contacts_table.item(row, 6)

            title = title_item.text() if title_item else ""
            initials = initials_item.text() if initials_item else ""
            names = names_item.text() if names_item else ""
            surname = surname_item.text() if surname_item else ""
            job_title = job_title_item.text() if job_title_item else ""
            telephone = telephone_item.text() if telephone_item else ""
            email = email_item.text() if email_item else ""

            # Require at least names or surname for a valid contact
            if names or surname:
                if email and not is_valid_email(email):
                    QMessageBox.warning(
                        self, "Invalid Email", f"Invalid email format: {email}"
                    )
                    return
                contacts.append(
                    {
                        "title": title,
                        "initials": initials,
                        "names": names,
                        "surname": surname,
                        "job_title": job_title,
                        "telephone": telephone,
                        "email": email,
                    }
                )
        return {
            "name": self.name_edit.text().strip(),
            "parent_id": self.parent_id,
            "is_posting_level": self.posting_yes.isChecked(),
            "contacts": contacts,
        }


class ResponsibilityManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Responsibilities")
        self.resize(1400, 700)
        self.responsibilities = []  # Initialize to prevent AttributeError
        self.setup_ui()
        self.load_responsibilities()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Left side layout (tree + search)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)

        # Search bar for responsibilities
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(10)

        search_label = QLabel("Search:")
        search_label.setFixedWidth(50)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search responsibilities...")
        self.search_edit.textChanged.connect(self.filter_responsibilities)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()

        left_layout.addLayout(search_layout)

        # Tree widget for responsibilities
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Responsibilities")
        self.tree.itemClicked.connect(self.load_responsibility)
        left_layout.addWidget(self.tree)

        layout.addLayout(left_layout, 3)  # Increased from 2 to 3 for more tree space

        # Form for responsibility details
        form_widget = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        self.name_edit = QLineEdit()
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

        form_widget.addLayout(form_layout)

        # Contacts table
        contacts_group = QGroupBox("Contacts")
        contacts_layout = QVBoxLayout()
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(7)
        self.contacts_table.setHorizontalHeaderLabels(
            ["Title", "Initials", "Names", "Surname", "Job Title", "Telephone", "Email"]
        )
        header = self.contacts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.contacts_table.setColumnWidth(0, 80)  # Title
        self.contacts_table.setColumnWidth(1, 80)  # Initials
        self.contacts_table.setColumnWidth(2, 120)  # Names
        self.contacts_table.setColumnWidth(3, 120)  # Surname
        self.contacts_table.setColumnWidth(4, 120)  # Job Title
        self.contacts_table.setColumnWidth(5, 120)  # Telephone
        self.contacts_table.setColumnWidth(6, 200)  # Email
        self.contacts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.contacts_table.setToolTip(
            "Click on cells to edit contacts. Use Add/Remove buttons or double-click to edit."
        )
        contacts_layout.addWidget(self.contacts_table)
        contacts_group.setLayout(contacts_layout)
        form_widget.addWidget(contacts_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_responsibility)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_responsibility)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_responsibility)
        self.up_button = QPushButton("Up")
        self.up_button.clicked.connect(self.move_up)
        self.down_button = QPushButton("Down")
        self.down_button.clicked.connect(self.move_down)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.up_button)
        button_layout.addWidget(self.down_button)
        form_widget.addLayout(button_layout)

        layout.addLayout(form_widget, 1)
        self.setLayout(layout)

    def load_responsibilities(self):
        self.tree.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, parent_id, is_posting_level, sort_order FROM responsibilities ORDER BY sort_order"
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
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Database Error", f"Failed to load responsibilities: {e}"
            )
            return

        parent_map = defaultdict(list)
        for resp in self.responsibilities:
            parent_map[resp["parent_id"]].append(resp)

        def add_items(parent_item, parent_id):
            for resp in sorted(
                parent_map[parent_id], key=lambda x: x.get("sort_order", 0)
            ):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_items(item, resp["id"])

        add_items(None, None)

    def load_responsibility(self, item):
        resp_id = item.data(0, Qt.UserRole)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, is_posting_level FROM responsibilities WHERE id = ?",
                (resp_id,),
            )
            result = cursor.fetchone()
            if result:
                self.name_edit.setText(result[0])
                if result[1]:
                    self.posting_yes.setChecked(True)
                else:
                    self.posting_no.setChecked(True)
            cursor.execute(
                "SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?",
                (resp_id,),
            )
            contacts = [
                {
                    "title": row[0],
                    "initials": row[1],
                    "names": row[2],
                    "surname": row[3],
                    "job_title": row[4],
                    "telephone": row[5],
                    "email": row[6],
                }
                for row in cursor.fetchall()
            ]
            conn.close()

            self.contacts_table.setRowCount(0)
            for contact in contacts:
                row = self.contacts_table.rowCount()
                self.contacts_table.insertRow(row)
                self.contacts_table.setItem(
                    row, 0, QTableWidgetItem(contact["title"] or "")
                )
                self.contacts_table.setItem(
                    row, 1, QTableWidgetItem(contact["initials"] or "")
                )
                self.contacts_table.setItem(
                    row, 2, QTableWidgetItem(contact["names"] or "")
                )
                self.contacts_table.setItem(
                    row, 3, QTableWidgetItem(contact["surname"] or "")
                )
                self.contacts_table.setItem(
                    row, 4, QTableWidgetItem(contact["job_title"] or "")
                )
                self.contacts_table.setItem(
                    row, 5, QTableWidgetItem(contact["telephone"] or "")
                )
                self.contacts_table.setItem(
                    row, 6, QTableWidgetItem(contact["email"] or "")
                )
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Database Error", f"Failed to load responsibility details: {e}"
            )

    def add_responsibility(self):
        selected_item = self.tree.currentItem()
        parent_id = selected_item.data(0, Qt.UserRole) if selected_item else None
        parent_name = selected_item.text(0) if selected_item else None
        inherited_contacts = []
        if parent_id:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                current_id = parent_id
                while current_id:
                    cursor.execute(
                        "SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?",
                        (current_id,),
                    )
                    inherited_contacts.extend(
                        [
                            {
                                "title": row[0],
                                "initials": row[1],
                                "names": row[2],
                                "surname": row[3],
                                "job_title": row[4],
                                "telephone": row[5],
                                "email": row[6],
                            }
                            for row in cursor.fetchall()
                        ]
                    )
                    cursor.execute(
                        "SELECT parent_id FROM responsibilities WHERE id = ?",
                        (current_id,),
                    )
                    result = cursor.fetchone()
                    current_id = result[0] if result else None
                conn.close()
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self, "Database Error", f"Failed to load inherited contacts: {e}"
                )
                return

        dialog = AddResponsibilityDialog(
            self, parent_id, parent_name, inherited_contacts
        )
        if dialog.exec_():
            data = dialog.get_data()
            data["inherited_contacts"] = inherited_contacts
            add_responsibility(self, data)

    def edit_responsibility(self):
        edit_responsibility(self)

    def delete_responsibility(self):
        delete_responsibility(self)

    def move_up(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            return
        parent = selected_item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(selected_item)
        if index > 0:
            parent.takeChild(index)
            parent.insertChild(index - 1, selected_item)
            self.tree.setCurrentItem(selected_item)
            self.update_sort_order(parent)

    def move_down(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            return
        parent = selected_item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(selected_item)
        if index < parent.childCount() - 1:
            parent.takeChild(index)
            parent.insertChild(index + 1, selected_item)
            self.tree.setCurrentItem(selected_item)
            self.update_sort_order(parent)

    def update_sort_order(self, parent_item):
        try:
            from Utilities.utils import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if parent_item == self.tree.invisibleRootItem():
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    resp_id = item.data(0, Qt.UserRole)
                    cursor.execute(
                        "UPDATE responsibilities SET sort_order = ? WHERE id = ?",
                        (i, resp_id),
                    )
            else:
                for i in range(parent_item.childCount()):
                    item = parent_item.child(i)
                    resp_id = item.data(0, Qt.UserRole)
                    cursor.execute(
                        "UPDATE responsibilities SET sort_order = ? WHERE id = ?",
                        (i, resp_id),
                    )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Database Error", f"Failed to update sort order: {e}"
            )

    def clear_form(self):
        self.contacts_table.setRowCount(0)

    def refresh_tree(self):
        selected_id = None
        expanded_ids = []
        current_item = self.tree.currentItem()
        if current_item:
            selected_id = current_item.data(0, Qt.UserRole)
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self._collect_expanded(item, expanded_ids)

        self.load_responsibilities()

        if selected_id:
            self._restore_selection(selected_id)
        for exp_id in expanded_ids:
            self._restore_expanded(exp_id)

    def _collect_expanded(self, item, expanded_ids):
        if item.isExpanded():
            expanded_ids.append(item.data(0, Qt.UserRole))
        for i in range(item.childCount()):
            self._collect_expanded(item.child(i), expanded_ids)

    def _restore_selection(self, selected_id):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if self._find_and_select_item(item, selected_id):
                break

    def _find_and_select_item(self, item, selected_id):
        if item.data(0, Qt.UserRole) == selected_id:
            self.tree.setCurrentItem(item)
            return True
        for i in range(item.childCount()):
            if self._find_and_select_item(item.child(i), selected_id):
                return True
        return False

    def _restore_expanded(self, exp_id):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if self._find_and_expand_item(item, exp_id):
                break

    def _find_and_expand_item(self, item, exp_id):
        if item.data(0, Qt.UserRole) == exp_id:
            item.setExpanded(True)
            return True
        for i in range(item.childCount()):
            if self._find_and_expand_item(item.child(i), exp_id):
                return True
        return False

    def filter_responsibilities(self, text):
        """Filter responsibilities based on search text"""
        text = text.lower().strip()
        if not text:
            self.load_responsibilities()
            return

        self.tree.clear()

        # Find responsibilities that match the search text
        matching_resps = []
        parent_ids_to_include = set()

        for resp in self.responsibilities:
            if text in resp["name"].lower():
                matching_resps.append(resp)
                # Also include the parent if it exists
                if resp["parent_id"]:
                    parent_ids_to_include.add(resp["parent_id"])

        # Include parent responsibilities recursively
        def add_parent_hierarchy(resp_id):
            for resp in self.responsibilities:
                if resp["id"] == resp_id:
                    if resp not in matching_resps:
                        matching_resps.append(resp)
                    if resp["parent_id"]:
                        add_parent_hierarchy(resp["parent_id"])
                    break

        for parent_id in parent_ids_to_include:
            add_parent_hierarchy(parent_id)

        # Remove duplicates while preserving order
        seen_ids = set()
        filtered_resps = []
        for resp in matching_resps:
            if resp["id"] not in seen_ids:
                filtered_resps.append(resp)
                seen_ids.add(resp["id"])

        # Create parent map for filtered results
        parent_map = defaultdict(list)
        for resp in filtered_resps:
            parent_map[resp["parent_id"]].append(resp)

        def add_filtered_items(parent_item, parent_id):
            if parent_id not in parent_map:
                return
            items = parent_map[parent_id]
            for resp in sorted(items, key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        self.tree.expandAll()
        self.tree.update()
