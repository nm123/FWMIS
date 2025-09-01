from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QComboBox,
    QDialogButtonBox,
    QWidget,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.list_utils import save_lists, load_lists
from scripts.Utilities.config import DB_PATH
import sqlite3
import logging

class ManageListsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Lists")
        self.setFixedSize(700, 500)
        self.lists = load_lists()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Tree widget for displaying lists
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Lists")
        layout.addWidget(self.tree, 2)

        # Buttons panel
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)

        self.add_button = QPushButton("Add List")
        self.add_button.clicked.connect(self.add_list)
        self.add_button.setMinimumHeight(35)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit List")
        self.edit_button.clicked.connect(self.edit_list)
        self.edit_button.setMinimumHeight(35)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete List")
        self.delete_button.clicked.connect(self.delete_list)
        self.delete_button.setMinimumHeight(35)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()
        layout.addWidget(button_widget, 1)

        self.setLayout(layout)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        self.lists = load_lists()
        # Create dict of id to list
        list_dict = {lst["id"]: lst for lst in self.lists}
        # Create dict of id to item
        item_dict = {}
        for lst in self.lists:
            display_name = lst["name"]
            if lst.get("is_system", False):
                display_name += " [System]"
            item = QTreeWidgetItem([display_name])
            item.setData(0, Qt.UserRole, lst["id"])
            # Disable system items
            if lst.get("is_system", False):
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item_dict[lst["id"]] = item
        # Add to tree hierarchically
        for lst in self.lists:
            parent_id = lst["parent_id"]
            if parent_id is None or parent_id not in item_dict:
                self.tree.addTopLevelItem(item_dict[lst["id"]])
            else:
                parent_item = item_dict[parent_id]
                parent_item.addChild(item_dict[lst["id"]])

    def get_selected_list(self):
        """Get the currently selected list from the tree"""
        selected = self.tree.selectedItems()
        if selected:
            list_id = selected[0].data(0, Qt.UserRole)
            return next((l for l in self.lists if l["id"] == list_id), None)
        return None

    def add_list(self):
        try:
            dialog = AddListDialog(self, self.lists)
            if dialog.exec_():
                list_data = dialog.get_list_data()

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(id) FROM lists")
                max_id = cursor.fetchone()[0]
                new_id = (max_id or 0) + 1

                new_list = {
                    "id": new_id,
                    "name": list_data["name"],
                    "parent_id": list_data["parent_id"],
                    "is_default": list_data["is_default"]
                }

                # If setting as default, unset others
                if list_data["is_default"]:
                    for lst in self.lists:
                        lst["is_default"] = False

                self.lists.append(new_list)
                save_lists(self.lists)

                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "List added successfully.")
                self.refresh_tree()
        except sqlite3.Error as e:
            logging.error(f"Failed to add list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add list: {str(e)}")

    def edit_list(self):
        selected_list = self.get_selected_list()
        if not selected_list:
            QMessageBox.warning(self, "No Selection", "Please select a list to edit.")
            return

        # Check if it's a system list
        if selected_list.get("is_system", False):
            QMessageBox.warning(self, "Cannot Edit", "Cannot edit system lists. They are required for the application workflow.")
            return

        try:
            dialog = EditListDialog(self, selected_list, self.lists)
            if dialog.exec_():
                list_data = dialog.get_list_data()

                for lst in self.lists:
                    if lst["id"] == selected_list["id"]:
                        lst["name"] = list_data["name"]
                        lst["parent_id"] = list_data["parent_id"]
                        lst["is_default"] = list_data["is_default"]
                        break

                # If setting as default, unset others
                if list_data["is_default"]:
                    for lst in self.lists:
                        if lst["id"] != selected_list["id"]:
                            lst["is_default"] = False

                save_lists(self.lists)

                QMessageBox.information(self, "Success", "List edited successfully.")
                self.refresh_tree()
        except sqlite3.Error as e:
            logging.error(f"Failed to edit list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit list: {str(e)}")

    def delete_list(self):
        selected_list = self.get_selected_list()
        if not selected_list:
            QMessageBox.warning(self, "No Selection", "Please select a list to delete.")
            return

        list_id = selected_list["id"]
        list_name = selected_list["name"]

        # Check if it's a system list
        if selected_list.get("is_system", False):
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete system lists. They are required for the application workflow.")
            return

        # Check if list has children
        if any(l["parent_id"] == list_id for l in self.lists):
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete a list with sublists.")
            return

        # Check if list is used in cases
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cases WHERE list = ?", (list_name,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Cannot Delete", "Cannot delete a list used in cases.")
                conn.close()
                return
            conn.close()
        except sqlite3.Error as e:
            logging.error(f"Failed to check cases for list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to check cases: {str(e)}")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete list '{list_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.lists = [l for l in self.lists if l["id"] != list_id]
                save_lists(self.lists)
                QMessageBox.information(self, "Success", "List deleted successfully.")
                self.refresh_tree()
            except sqlite3.Error as e:
                logging.error(f"Failed to delete list: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete list: {str(e)}")

    def would_create_cycle(self, parent_id, lists, editing_id=None):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            if current_id == editing_id:  # Prevent self-referencing during edit
                return True
            parent = next((l["parent_id"] for l in lists if l["id"] == current_id), None)
            current_id = parent
        return False


class AddListDialog(QDialog):
    def __init__(self, parent=None, lists=None):
        super().__init__(parent)
        self.setWindowTitle("Add New List")
        self.setFixedSize(400, 250)
        self.lists = lists or []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Enter a unique list name, max 100 characters")
        form_layout.addRow("Name:", self.name_edit)

        # Parent list dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.setToolTip("Select a parent list or 'None' for top-level")
        self.parent_combo.addItem("None", None)
        for lst in self.lists:
            self.parent_combo.addItem(lst["name"], lst["id"])
        form_layout.addRow("Parent:", self.parent_combo)

        # Default list checkbox
        self.default_check = QCheckBox("Set as default list")
        self.default_check.setToolTip("Check to make this the default list for new cases")
        form_layout.addRow("", self.default_check)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_list)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_list(self):
        name = self.name_edit.text().strip()
        parent_id = self.parent_combo.currentData()
        is_default = self.default_check.isChecked()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        if any(l["name"] == name for l in self.lists):
            QMessageBox.warning(self, "Invalid Input", "List name must be unique.")
            return

        # Check for circular reference
        if parent_id and self.would_create_cycle(parent_id, self.lists):
            QMessageBox.warning(self, "Invalid Input", "Cannot create circular parent-child relationship.")
            return

        self.accept()

    def would_create_cycle(self, parent_id, lists):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            parent = next((l["parent_id"] for l in lists if l["id"] == current_id), None)
            current_id = parent
        return False

    def get_list_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "parent_id": self.parent_combo.currentData(),
            "is_default": self.default_check.isChecked()
        }


class EditListDialog(QDialog):
    def __init__(self, parent=None, list_item=None, lists=None):
        super().__init__(parent)
        self.setWindowTitle("Edit List")
        self.setFixedSize(400, 250)
        self.list_item = list_item
        self.lists = lists or []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_edit = QLineEdit(self.list_item["name"])
        self.name_edit.setToolTip("Enter a unique list name, max 100 characters")
        form_layout.addRow("Name:", self.name_edit)

        # Parent list dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.setToolTip("Select a parent list or 'None' for top-level")
        self.parent_combo.addItem("None", None)
        for lst in self.lists:
            self.parent_combo.addItem(lst["name"], lst["id"])

        # Set current parent
        current_parent_id = self.list_item["parent_id"]
        index = self.parent_combo.findData(current_parent_id)
        self.parent_combo.setCurrentIndex(index if index >= 0 else 0)
        form_layout.addRow("Parent:", self.parent_combo)

        # Default list checkbox
        self.default_check = QCheckBox("Set as default list")
        self.default_check.setToolTip("Check to make this the default list for new cases")
        self.default_check.setChecked(self.list_item.get("is_default", False))
        form_layout.addRow("", self.default_check)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_list)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_list(self):
        name = self.name_edit.text().strip()
        parent_id = self.parent_combo.currentData()
        is_default = self.default_check.isChecked()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        if any(l["name"] == name and l["id"] != self.list_item["id"] for l in self.lists):
            QMessageBox.warning(self, "Invalid Input", "List name must be unique.")
            return

        if parent_id and (parent_id == self.list_item["id"] or self.would_create_cycle(parent_id, self.lists, self.list_item["id"])):
            QMessageBox.warning(self, "Invalid Input", "Cannot create circular parent-child relationship.")
            return

        self.accept()

    def would_create_cycle(self, parent_id, lists, editing_id=None):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            if current_id == editing_id:  # Prevent self-referencing during edit
                return True
            parent = next((l["parent_id"] for l in lists if l["id"] == current_id), None)
            current_id = parent
        return False

    def get_list_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "parent_id": self.parent_combo.currentData(),
            "is_default": self.default_check.isChecked()
        }


def manage_lists(app):
    dialog = ManageListsDialog(app)
    dialog.exec_()