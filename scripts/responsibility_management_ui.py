import sqlite3
import os
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QRadioButton, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from responsibility_management_actions import add_responsibility, edit_responsibility, delete_responsibility
from utils import BASE_DIR, is_valid_email

class AddResponsibilityDialog(QDialog):
    def __init__(self, parent=None, parent_id=None, parent_name=None, inherited_contacts=None):
        super().__init__(parent)
        self.setWindowTitle("Add Child Responsibility")
        self.resize(600, 500)
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
        self.parent_label.setToolTip("Parent responsibility (selected from main dialog)")
        form_layout.addRow("Parent:", self.parent_label)

        # Name input
        self.name_edit = QLineEdit(self)
        self.name_edit.setToolTip("Enter a unique responsibility name, max 100 characters")
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
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(["Name", "Title", "Telephone", "Email"])
        header = self.contacts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.contacts_table.setColumnWidth(0, 150)  # Name
        self.contacts_table.setColumnWidth(1, 100)  # Title
        self.contacts_table.setColumnWidth(2, 120)  # Telephone
        self.contacts_table.setColumnWidth(3, 200)  # Email
        self.contacts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.setEditTriggers(QTableWidget.DoubleClicked)  # Enable direct editing
        contacts_layout.addWidget(self.contacts_table)
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)

        # Populate inherited contacts (non-editable)
        for contact in self.inherited_contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)
            self.contacts_table.setItem(row, 0, QTableWidgetItem(contact["name"]))
            self.contacts_table.setItem(row, 1, QTableWidgetItem(contact["title"] or ""))
            self.contacts_table.setItem(row, 2, QTableWidgetItem(contact["telephone"] or ""))
            self.contacts_table.setItem(row, 3, QTableWidgetItem(contact["email"]))
            for col in range(4):
                item = self.contacts_table.item(row, col)
                if item:
                    item.setFont(QFont("Arial", 10, QFont.StyleItalic))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Disable editing for inherited
                    item.setToolTip("Inherited from parent")

        # Contact buttons
        contact_buttons = QHBoxLayout()
        self.add_contact_btn = QPushButton("Add Contact", self)
        self.add_contact_btn.clicked.connect(self.add_contact)
        self.delete_contact_btn = QPushButton("Delete Contact", self)
        self.delete_contact_btn.clicked.connect(self.delete_contact)
        contact_buttons.addWidget(self.add_contact_btn)
        contact_buttons.addWidget(self.delete_contact_btn)
        layout.addLayout(contact_buttons)

        # Action buttons
        action_buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save", self)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        action_buttons.addStretch()
        action_buttons.addWidget(self.save_btn)
        action_buttons.addWidget(self.cancel_btn)
        layout.addLayout(action_buttons)

    def add_contact(self):
        row = self.contacts_table.rowCount()
        self.contacts_table.insertRow(row)
        self.contacts_table.setItem(row, 0, QTableWidgetItem(""))
        self.contacts_table.setItem(row, 1, QTableWidgetItem(""))
        self.contacts_table.setItem(row, 2, QTableWidgetItem(""))
        self.contacts_table.setItem(row, 3, QTableWidgetItem(""))
        self.contacts_table.selectRow(row)
        self.contacts_table.editItem(self.contacts_table.item(row, 0))  # Start editing first column

    def delete_contact(self):
        selected = self.contacts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a contact to delete.")
            return
        row = self.contacts_table.currentRow()
        if row < len(self.inherited_contacts):
            QMessageBox.warning(self, "Invalid Action", "Cannot delete inherited contacts.")
            return
        self.contacts_table.removeRow(row)

    def get_data(self):
        name = self.name_edit.text().strip()
        is_posting_level = self.posting_yes.isChecked()
        contacts = []
        for row in range(self.contacts_table.rowCount()):
            name_item = self.contacts_table.item(row, 0)
            title_item = self.contacts_table.item(row, 1)
            telephone_item = self.contacts_table.item(row, 2)
            email_item = self.contacts_table.item(row, 3)
            name_text = name_item.text().strip() if name_item else ""
            title = title_item.text().strip() if title_item else ""
            telephone = telephone_item.text().strip() if telephone_item else ""
            email = email_item.text().strip() if email_item else ""
            # Only include non-inherited contacts (editable rows)
            if row >= len(self.inherited_contacts) and name_text and title and email:
                contacts.append({"name": name_text, "title": title, "telephone": telephone, "email": email})
        data = {
            "name": name,
            "parent_id": self.parent_id,
            "is_posting_level": is_posting_level,
            "contacts": contacts,
            "inherited_contacts": self.inherited_contacts
        }
        print(f"AddResponsibilityDialog.get_data: {data}")
        return data

class ResponsibilityManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Responsibilities")
        self.resize(1000, 800)
        self.responsibilities = []
        self.setup_ui()
        self.load_responsibilities()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Action buttons
        action_buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add", self)
        self.add_btn.setToolTip("Add a new child responsibility")
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn = QPushButton("Edit", self)
        self.edit_btn.setToolTip("Edit the selected responsibility")
        self.edit_btn.clicked.connect(self.edit_responsibility)
        self.delete_btn = QPushButton("Delete", self)
        self.delete_btn.setToolTip("Delete the selected responsibility")
        self.delete_btn.clicked.connect(self.delete_responsibility)
        action_buttons.addWidget(self.add_btn)
        action_buttons.addWidget(self.edit_btn)
        action_buttons.addWidget(self.delete_btn)
        action_buttons.addStretch()
        layout.addLayout(action_buttons)

        # Tree for responsibilities
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Responsibilities")
        self.tree.setColumnCount(1)
        self.tree.itemSelectionChanged.connect(self.load_selected_responsibility)
        layout.addWidget(self.tree)

        # Contacts table
        contacts_group = QGroupBox("Contacts")
        contacts_layout = QVBoxLayout()
        self.contacts_table = QTableWidget(self)
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(["Name", "Title", "Telephone", "Email"])
        header = self.contacts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.contacts_table.setColumnWidth(0, 150)  # Name
        self.contacts_table.setColumnWidth(1, 100)  # Title
        self.contacts_table.setColumnWidth(2, 120)  # Telephone
        self.contacts_table.setColumnWidth(3, 200)  # Email
        self.contacts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only
        contacts_layout.addWidget(self.contacts_table)
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)

    def load_responsibilities(self):
        self.tree.clear()
        try:
            db_path = os.path.join(BASE_DIR, "fruitless.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities")
            self.responsibilities = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]
            conn.close()

            # Log loaded responsibilities for debugging
            print(f"Loaded responsibilities: {self.responsibilities}")

            # Build tree
            id_to_item = {}
            for resp in self.responsibilities:
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                font = QFont("Arial", 10)
                font.setBold(resp["is_posting_level"] == 0)  # Bold only for non-posting
                item.setFont(0, font)
                id_to_item[resp["id"]] = item
                if resp["parent_id"] is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item = id_to_item.get(resp["parent_id"])
                    if parent_item:
                        parent_item.addChild(item)
            self.tree.expandAll()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load responsibilities: {e}")

    def load_selected_responsibility(self):
        self.contacts_table.setRowCount(0)
        selected_item = self.tree.currentItem()
        if not selected_item:
            return
        resp_id = selected_item.data(0, Qt.UserRole)
        try:
            db_path = os.path.join(BASE_DIR, "fruitless.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, title, telephone, email FROM contacts WHERE responsibility_id = ?", (resp_id,))
            for row in cursor.fetchall():
                row_count = self.contacts_table.rowCount()
                self.contacts_table.insertRow(row_count)
                self.contacts_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
                self.contacts_table.setItem(row_count, 1, QTableWidgetItem(row[1] or ""))
                self.contacts_table.setItem(row_count, 2, QTableWidgetItem(row[2] or ""))
                self.contacts_table.setItem(row_count, 3, QTableWidgetItem(row[3]))
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load contacts: {e}")

    def open_add_dialog(self):
        selected_item = self.tree.currentItem()
        parent_id = None
        parent_name = "None"
        inherited_contacts = []
        if selected_item:
            parent_id = selected_item.data(0, Qt.UserRole)
            parent_name = selected_item.text(0)
            try:
                db_path = os.path.join(BASE_DIR, "fruitless.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name, title, telephone, email FROM contacts WHERE responsibility_id = ?", (parent_id,))
                inherited_contacts = [{"name": row[0], "title": row[1] or "", "telephone": row[2] or "", "email": row[3]} for row in cursor.fetchall()]
                conn.close()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to load parent contacts: {e}")
                return
        dialog = AddResponsibilityDialog(self, parent_id, parent_name, inherited_contacts)
        if dialog.exec_():
            data = dialog.get_data()
            add_responsibility(self, data)

    def edit_responsibility(self):
        edit_responsibility(self)

    def delete_responsibility(self):
        delete_responsibility(self)

    def clear_form(self):
        self.contacts_table.setRowCount(0)

    def refresh_tree(self):
        # Save current selection and expansion state
        selected_id = None
        expanded_ids = []
        current_item = self.tree.currentItem()
        if current_item:
            selected_id = current_item.data(0, Qt.UserRole)
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self._collect_expanded(item, expanded_ids)

        # Reload responsibilities
        self.load_responsibilities()

        # Restore selection and expansion state
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