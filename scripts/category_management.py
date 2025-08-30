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
    QGroupBox,
    QRadioButton,
    QLabel,
    QDialogButtonBox,
    QWidget,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from Utilities.utils import save_categories, load_categories, DB_PATH
import sqlite3
import logging

class ManageCategoriesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setFixedSize(700, 500)
        self.categories = load_categories()
        self.setup_ui()


    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Tree widget for displaying categories
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Categories")
        layout.addWidget(self.tree, 2)

        # Buttons panel
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)

        self.add_button = QPushButton("Add Category")
        self.add_button.clicked.connect(self.add_category)
        self.add_button.setMinimumHeight(35)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Category")
        self.edit_button.clicked.connect(self.edit_category)
        self.edit_button.setMinimumHeight(35)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Category")
        self.delete_button.clicked.connect(self.delete_category)
        self.delete_button.setMinimumHeight(35)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()
        layout.addWidget(button_widget, 1)

        self.setLayout(layout)
        self.refresh_tree()


    def refresh_tree(self):
        self.tree.clear()
        self.categories = load_categories()
        # Create dict of id to category
        cat_dict = {cat["id"]: cat for cat in self.categories}
        # Create dict of id to item
        item_dict = {}
        for cat in self.categories:
            item = QTreeWidgetItem([cat["name"]])
            item.setData(0, Qt.UserRole, cat["id"])
            item_dict[cat["id"]] = item
        # Add to tree hierarchically
        for cat in self.categories:
            parent_id = cat["parent_id"]
            if parent_id is None or parent_id not in item_dict:
                self.tree.addTopLevelItem(item_dict[cat["id"]])
            else:
                parent_item = item_dict[parent_id]
                parent_item.addChild(item_dict[cat["id"]])

    def get_selected_category(self):
        """Get the currently selected category from the tree"""
        selected = self.tree.selectedItems()
        if selected:
            cat_id = selected[0].data(0, Qt.UserRole)
            return next((c for c in self.categories if c["id"] == cat_id), None)
        return None

    def add_category(self):
        try:
            dialog = AddCategoryDialog(self, self.categories)
            if dialog.exec_():
                category_data = dialog.get_category_data()

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(id) FROM categories")
                max_id = cursor.fetchone()[0]
                new_id = (max_id or 0) + 1

                new_category = {
                    "id": new_id,
                    "name": category_data["name"],
                    "parent_id": category_data["parent_id"],
                    "persal_compulsory": category_data["persal_compulsory"],
                    "bas_payment_compulsory": category_data["bas_payment_compulsory"]
                }
                self.categories.append(new_category)
                save_categories(self.categories)

                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "Category added successfully.")
                self.refresh_tree()
        except sqlite3.Error as e:
            logging.error(f"Failed to add category: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add category: {str(e)}")

    def edit_category(self):
        selected_category = self.get_selected_category()
        if not selected_category:
            QMessageBox.warning(self, "No Selection", "Please select a category to edit.")
            return

        try:
            dialog = EditCategoryDialog(self, selected_category, self.categories)
            if dialog.exec_():
                category_data = dialog.get_category_data()

                for category in self.categories:
                    if category["id"] == selected_category["id"]:
                        category["name"] = category_data["name"]
                        category["parent_id"] = category_data["parent_id"]
                        category["persal_compulsory"] = category_data["persal_compulsory"]
                        category["bas_payment_compulsory"] = category_data["bas_payment_compulsory"]
                        break

                save_categories(self.categories)

                QMessageBox.information(self, "Success", "Category edited successfully.")
                self.refresh_tree()
        except sqlite3.Error as e:
            logging.error(f"Failed to edit category: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit category: {str(e)}")

    def delete_category(self):
        selected_category = self.get_selected_category()
        if not selected_category:
            QMessageBox.warning(self, "No Selection", "Please select a category to delete.")
            return

        cat_id = selected_category["id"]
        category_name = selected_category["name"]

        # Check if category has children
        if any(c["parent_id"] == cat_id for c in self.categories):
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete a category with subcategories.")
            return

        # Check if category is used in cases
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cases WHERE category = ?", (category_name,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Cannot Delete", "Cannot delete a category used in cases.")
                conn.close()
                return
            conn.close()
        except sqlite3.Error as e:
            logging.error(f"Failed to check cases for category: {e}")
            QMessageBox.critical(self, "Error", f"Failed to check cases: {str(e)}")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete category '{category_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.categories = [c for c in self.categories if c["id"] != cat_id]
                save_categories(self.categories)
                QMessageBox.information(self, "Success", "Category deleted successfully.")
                self.refresh_tree()
            except sqlite3.Error as e:
                logging.error(f"Failed to delete category: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete category: {str(e)}")

    def would_create_cycle(self, parent_id, categories, editing_id=None):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            if current_id == editing_id:  # Prevent self-referencing during edit
                return True
            parent = next((c["parent_id"] for c in categories if c["id"] == current_id), None)
            current_id = parent
        return False


class AddCategoryDialog(QDialog):
    def __init__(self, parent=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Category")
        self.setFixedSize(400, 300)
        self.categories = categories or []
        self.persal_compulsory = False
        self.bas_payment_compulsory = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Enter a unique category name, max 100 characters")
        form_layout.addRow("Name:", self.name_edit)

        # Parent category dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.setToolTip("Select a parent category or 'None' for top-level")
        self.parent_combo.addItem("None", None)
        for category in self.categories:
            self.parent_combo.addItem(category["name"], category["id"])
        form_layout.addRow("Parent:", self.parent_combo)

        layout.addLayout(form_layout)

        # Compulsory Fields Settings
        settings_group = QGroupBox("Case Form Settings")
        settings_layout = QVBoxLayout()

        # Persal No compulsory setting
        self.persal_check = QCheckBox("Persal No is compulsory")
        self.persal_check.setChecked(False)
        settings_layout.addWidget(self.persal_check)

        # BAS Payment No compulsory setting
        self.bas_check = QCheckBox("BAS Payment No is compulsory")
        self.bas_check.setChecked(False)
        settings_layout.addWidget(self.bas_check)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_category)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_category(self):
        name = self.name_edit.text().strip()
        parent_id = self.parent_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        if any(c["name"] == name for c in self.categories):
            QMessageBox.warning(self, "Invalid Input", "Category name must be unique.")
            return

        # Check for circular reference
        if parent_id and self.would_create_cycle(parent_id, self.categories):
            QMessageBox.warning(self, "Invalid Input", "Cannot create circular parent-child relationship.")
            return

        # Set compulsory settings
        self.persal_compulsory = self.persal_check.isChecked()
        self.bas_payment_compulsory = self.bas_check.isChecked()

        self.accept()

    def would_create_cycle(self, parent_id, categories):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            parent = next((c["parent_id"] for c in categories if c["id"] == current_id), None)
            current_id = parent
        return False

    def get_category_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "parent_id": self.parent_combo.currentData(),
            "persal_compulsory": self.persal_compulsory,
            "bas_payment_compulsory": self.bas_payment_compulsory
        }


class EditCategoryDialog(QDialog):
    def __init__(self, parent=None, category=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Category")
        self.setFixedSize(400, 300)
        self.category = category
        self.categories = categories or []
        self.persal_compulsory = category.get("persal_compulsory", False)
        self.bas_payment_compulsory = category.get("bas_payment_compulsory", False)
        self.setup_ui()


    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_edit = QLineEdit(self.category["name"])
        self.name_edit.setToolTip("Enter a unique category name, max 100 characters")
        form_layout.addRow("Name:", self.name_edit)

        # Parent category dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.setToolTip("Select a parent category or 'None' for top-level")
        self.parent_combo.addItem("None", None)
        for category in self.categories:
            self.parent_combo.addItem(category["name"], category["id"])

        # Set current parent
        current_parent_id = self.category["parent_id"]
        index = self.parent_combo.findData(current_parent_id)
        self.parent_combo.setCurrentIndex(index if index >= 0 else 0)
        form_layout.addRow("Parent:", self.parent_combo)

        layout.addLayout(form_layout)

        # Compulsory Fields Settings
        settings_group = QGroupBox("Case Form Settings")
        settings_layout = QVBoxLayout()

        # Persal No compulsory setting
        self.persal_check = QCheckBox("Persal No is compulsory")
        self.persal_check.setChecked(self.persal_compulsory)
        settings_layout.addWidget(self.persal_check)

        # BAS Payment No compulsory setting
        self.bas_check = QCheckBox("BAS Payment No is compulsory")
        self.bas_check.setChecked(self.bas_payment_compulsory)
        settings_layout.addWidget(self.bas_check)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_category)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_category(self):
        name = self.name_edit.text().strip()
        parent_id = self.parent_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        if any(c["name"] == name and c["id"] != self.category["id"] for c in self.categories):
            QMessageBox.warning(self, "Invalid Input", "Category name must be unique.")
            return

        if parent_id and (parent_id == self.category["id"] or self.would_create_cycle(parent_id, self.categories, self.category["id"])):
            QMessageBox.warning(self, "Invalid Input", "Cannot create circular parent-child relationship.")
            return

        # Set compulsory settings
        self.persal_compulsory = self.persal_check.isChecked()
        self.bas_payment_compulsory = self.bas_check.isChecked()

        self.accept()

    def would_create_cycle(self, parent_id, categories, editing_id=None):
        """Check if assigning parent_id would create a circular reference."""
        seen = set()
        current_id = parent_id
        while current_id:
            if current_id in seen:
                return True
            seen.add(current_id)
            if current_id == editing_id:  # Prevent self-referencing during edit
                return True
            parent = next((c["parent_id"] for c in categories if c["id"] == current_id), None)
            current_id = parent
        return False

    def get_category_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "parent_id": self.parent_combo.currentData(),
            "persal_compulsory": self.persal_compulsory,
            "bas_payment_compulsory": self.bas_payment_compulsory
        }


def manage_categories(app):
    dialog = ManageCategoriesDialog(app)
    dialog.exec_()