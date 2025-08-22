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
)
from PyQt5.QtCore import Qt
from utils import save_categories, load_categories

class ManageCategoriesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setFixedSize(600, 400)
        self.categories = load_categories()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Categories")
        self.tree.itemClicked.connect(self.load_category)
        layout.addWidget(self.tree, 1)
        form_widget = QVBoxLayout()
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        form_widget.addLayout(form_layout)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_category)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_category)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_category)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        form_widget.addLayout(button_layout)
        layout.addLayout(form_widget, 1)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        self.categories = load_categories()
        for category in self.categories:
            item = QTreeWidgetItem([category["name"]])
            item.setData(0, Qt.UserRole, category["id"])
            self.tree.addTopLevelItem(item)

    def load_category(self, item):
        cat_id = item.data(0, Qt.UserRole)
        category = next((c for c in self.categories if c["id"] == cat_id), None)
        if category:
            self.name_edit.setText(category["name"])

    def add_category(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Name is required.")
                return
            if any(c["name"] == name for c in self.categories):
                QMessageBox.warning(self, "Invalid Input", "Category name must be unique.")
                return
            max_id = max((c["id"] for c in self.categories), default=0) + 1
            new_category = {"id": max_id, "name": name}
            self.categories.append(new_category)
            save_categories(self.categories)
            self.refresh_tree()
            self.name_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add category: {str(e)}")

    def edit_category(self):
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a category to edit.")
            return
        try:
            cat_id = selected[0].data(0, Qt.UserRole)
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Name is required.")
                return
            if any(c["name"] == name and c["id"] != cat_id for c in self.categories):
                QMessageBox.warning(self, "Invalid Input", "Category name must be unique.")
                return
            for category in self.categories:
                if category["id"] == cat_id:
                    category["name"] = name
                    break
            save_categories(self.categories)
            self.refresh_tree()
            self.name_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit category: {str(e)}")

    def delete_category(self):
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a category to delete.")
            return
        cat_id = selected[0].data(0, Qt.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete category {selected[0].text(0)}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.categories = [c for c in self.categories if c["id"] != cat_id]
            save_categories(self.categories)
            self.refresh_tree()
            self.name_edit.clear()

def manage_categories(app):
    dialog = ManageCategoriesDialog(app)
    dialog.exec_()