import sqlite3
from collections import defaultdict
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.config import DB_PATH


class ResponsibilitySelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Responsibility")
        self.setFixedSize(800, 600)
        self.selected_responsibility = None
        self.responsibilities = []  # Initialize to prevent AttributeError
        self.setup_ui()
        self.load_responsibilities()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search responsibilities...")
        self.search_edit.textChanged.connect(self.filter_responsibilities)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Posting Level Responsibilities")
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_responsibility)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def load_responsibilities(self):
        self.tree.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # First, get all posting level responsibilities
            cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE is_posting_level = 1 ORDER BY name")
            posting_resps = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]

            # Get all unique parent IDs of posting responsibilities
            parent_ids = set()
            for resp in posting_resps:
                if resp["parent_id"]:
                    parent_ids.add(resp["parent_id"])

            # Load parent responsibilities (even if not posting level)
            parent_resps = []
            if parent_ids:
                placeholders = ",".join("?" for _ in parent_ids)
                cursor.execute(f"SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE id IN ({placeholders})", list(parent_ids))
                parent_resps = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]

            # Combine all responsibilities
            self.responsibilities = parent_resps + posting_resps
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load responsibilities: {e}")
            return

        # Debug prints removed for production

        parent_map = defaultdict(list)
        for resp in self.responsibilities:
            parent_map[resp["parent_id"]].append(resp)

        def add_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                item.setData(1, Qt.UserRole, resp["is_posting_level"])  # Store posting level status

                # Visual styling for non-posting items
                if resp["is_posting_level"] == 0:
                    font = item.font(0)
                    font.setItalic(True)
                    item.setFont(0, font)
                    item.setToolTip(0, "Non-posting level responsibility - cannot be selected")
                else:
                    item.setToolTip(0, "Posting level responsibility - can be selected")

                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_items(item, resp["id"])

        add_items(None, None)
        self.tree.expandAll()

    def filter_responsibilities(self, text):
        text = text.lower()
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

        # Include parent responsibilities
        for resp in self.responsibilities:
            if resp["id"] in parent_ids_to_include:
                matching_resps.append(resp)

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
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                item.setData(1, Qt.UserRole, resp["is_posting_level"])

                # Visual styling for non-posting items
                if resp["is_posting_level"] == 0:
                    font = item.font(0)
                    font.setItalic(True)
                    item.setFont(0, font)
                    item.setToolTip(0, "Non-posting level responsibility - cannot be selected")
                else:
                    item.setToolTip(0, "Posting level responsibility - can be selected")

                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        self.tree.expandAll()
        self.tree.update()

    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree item with validation"""
        self.select_responsibility()

    def select_responsibility(self):
        try:
            selected_item = self.tree.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "No Selection", "Please select a responsibility from the tree first.")
                return

            is_posting = selected_item.data(1, Qt.UserRole)  # Get posting level status

            if is_posting == 1:
                resp_id = selected_item.data(0, Qt.UserRole)
                resp_name = selected_item.text(0)

                if resp_id is None:
                    QMessageBox.critical(self, "Error", "Selected responsibility has no ID.")
                    return

                self.selected_responsibility = {"id": resp_id, "name": resp_name}
                self.accept()
            else:
                QMessageBox.warning(self, "Invalid Selection",
                                  "You can only select posting level responsibilities.\n\n"
                                  "Non-posting level responsibilities are shown in italics and cannot be selected.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while selecting the responsibility:\n\n{str(e)}")

    def get_selected_responsibility(self):
        return self.selected_responsibility