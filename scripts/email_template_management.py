from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.email_utils import load_email_templates, save_email_templates


class ManageEmailTemplatesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Email Templates")
        self.setFixedSize(600, 400)
        self.templates = load_email_templates()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Email Templates")
        self.tree.itemClicked.connect(self.load_template)
        layout.addWidget(self.tree, 1)
        form_widget = QVBoxLayout()
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText(
            "Enter email body with placeholders like [Recipient], [Case ID]"
        )
        form_layout.addRow("Body:", self.body_edit)
        form_widget.addLayout(form_layout)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_template)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_template)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_template)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        form_widget.addLayout(button_layout)
        layout.addLayout(form_widget, 1)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        self.templates = load_email_templates()
        for template in self.templates:
            item = QTreeWidgetItem([template["name"]])
            item.setData(0, Qt.UserRole, template["id"])
            self.tree.addTopLevelItem(item)

    def load_template(self, item):
        template_id = item.data(0, Qt.UserRole)
        template = next((t for t in self.templates if t["id"] == template_id), None)
        if template:
            self.name_edit.setText(template["name"])
            self.body_edit.setText(template["body"])

    def add_template(self):
        try:
            name = self.name_edit.text().strip()
            body = self.body_edit.toPlainText().strip()
            if not name or not body:
                QMessageBox.warning(
                    self, "Invalid Input", "Name and body are required."
                )
                return
            if any(t["name"] == name for t in self.templates):
                QMessageBox.warning(
                    self, "Invalid Input", "Template name must be unique."
                )
                return
            max_id = max((t["id"] for t in self.templates), default=0) + 1
            new_template = {"id": max_id, "name": name, "body": body}
            self.templates.append(new_template)
            save_email_templates(self.templates)
            self.refresh_tree()
            self.name_edit.clear()
            self.body_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add template: {str(e)}")

    def edit_template(self):
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "No Selection", "Please select a template to edit."
            )
            return
        try:
            template_id = selected[0].data(0, Qt.UserRole)
            name = self.name_edit.text().strip()
            body = self.body_edit.toPlainText().strip()
            if not name or not body:
                QMessageBox.warning(
                    self, "Invalid Input", "Name and body are required."
                )
                return
            if any(
                t["name"] == name and t["id"] != template_id for t in self.templates
            ):
                QMessageBox.warning(
                    self, "Invalid Input", "Template name must be unique."
                )
                return
            for template in self.templates:
                if template["id"] == template_id:
                    template["name"] = name
                    template["body"] = body
                    break
            save_email_templates(self.templates)
            self.refresh_tree()
            self.name_edit.clear()
            self.body_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit template: {str(e)}")

    def delete_template(self):
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "No Selection", "Please select a template to delete."
            )
            return
        template_id = selected[0].data(0, Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete template {selected[0].text(0)}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.templates = [t for t in self.templates if t["id"] != template_id]
            save_email_templates(self.templates)
            self.refresh_tree()
            self.name_edit.clear()
            self.body_edit.clear()


def manage_email_templates(app):
    dialog = ManageEmailTemplatesDialog(app)
    dialog.exec_()
