"""
UI Components Module for Responsibility Management

Contains shared UI components and utilities for responsibility management dialogs.
"""

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTableWidget, QWidget


class UIComponents:
    """
    Shared UI components and utilities for responsibility management.
    """

    @staticmethod
    def setup_contacts_table(table: "QTableWidget", readonly: bool = False) -> None:
        """
        Set up a contacts table with proper configuration.

        Args:
            table: The table widget to configure
            readonly: Whether the table should be read-only
        """
        from PyQt5.QtWidgets import QHeaderView

        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Title", "Initials", "Names", "Surname", "Job Title", "Telephone", "Email"]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        table.setColumnWidth(0, 80)  # Title
        table.setColumnWidth(1, 80)  # Initials
        table.setColumnWidth(2, 120)  # Names
        table.setColumnWidth(3, 120)  # Surname
        table.setColumnWidth(4, 120)  # Job Title
        table.setColumnWidth(5, 120)  # Telephone
        table.setColumnWidth(6, 200)  # Email

        table.setSelectionMode(table.SingleSelection)
        table.setSelectionBehavior(table.SelectRows)

        if not readonly:
            table.setEditTriggers(table.AllEditTriggers)
            table.setToolTip(
                "Click on cells to edit contacts. Use Add/Remove buttons or double-click to edit."
            )
        else:
            table.setEditTriggers(table.NoEditTriggers)

    @staticmethod
    def add_contact_to_table(table: "QTableWidget", contact: Dict) -> None:
        """
        Add a contact to the table.

        Args:
            table: The table widget
            contact: Contact data dictionary
        """
        from PyQt5.QtWidgets import QTableWidgetItem

        row_count = table.rowCount()
        table.insertRow(row_count)

        table.setItem(row_count, 0, QTableWidgetItem(contact.get("title", "")))
        table.setItem(row_count, 1, QTableWidgetItem(contact.get("initials", "")))
        table.setItem(row_count, 2, QTableWidgetItem(contact.get("names", "")))
        table.setItem(row_count, 3, QTableWidgetItem(contact.get("surname", "")))
        table.setItem(row_count, 4, QTableWidgetItem(contact.get("job_title", "")))
        table.setItem(row_count, 5, QTableWidgetItem(contact.get("telephone", "")))
        table.setItem(row_count, 6, QTableWidgetItem(contact.get("email", "")))

    @staticmethod
    def get_contacts_from_table(table: "QTableWidget") -> List[Dict]:
        """
        Extract contacts data from the table.

        Args:
            table: The table widget

        Returns:
            List of contact dictionaries
        """
        contacts = []
        for row in range(table.rowCount()):
            contact_data = {
                "title": table.item(row, 0).text() if table.item(row, 0) else "",
                "initials": table.item(row, 1).text() if table.item(row, 1) else "",
                "names": table.item(row, 2).text() if table.item(row, 2) else "",
                "surname": table.item(row, 3).text() if table.item(row, 3) else "",
                "job_title": table.item(row, 4).text() if table.item(row, 4) else "",
                "telephone": table.item(row, 5).text() if table.item(row, 5) else "",
                "email": table.item(row, 6).text() if table.item(row, 6) else "",
            }
            # Only add if not completely empty
            if any(contact_data.values()):
                contacts.append(contact_data)

        return contacts

    @staticmethod
    def populate_contacts_table(table: "QTableWidget", contacts: List[Dict]) -> None:
        """
        Populate the contacts table with contact data.

        Args:
            table: The table widget
            contacts: List of contact dictionaries
        """
        table.setRowCount(0)  # Clear existing rows

        for contact in contacts:
            UIComponents.add_contact_to_table(table, contact)

    @staticmethod
    def create_tree_item(text: str, resp_id: int, is_posting_level: bool = False):
        """
        Create a tree widget item for the responsibility tree.

        Args:
            text: Display text
            resp_id: Responsibility ID
            is_posting_level: Whether this is a posting level responsibility

        Returns:
            QTreeWidgetItem: Configured tree item
        """
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QTreeWidgetItem

        item = QTreeWidgetItem([text])
        item.resp_id = resp_id
        item.is_posting_level = is_posting_level

        # Style posting level items
        if is_posting_level:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        return item

    @staticmethod
    def load_responsibility_tree(tree_widget: "QWidget") -> None:
        """
        Load the responsibility tree from the database.

        Args:
            tree_widget: The tree widget to populate
        """
        try:
            import sqlite3
            from collections import defaultdict

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get all responsibilities
            cursor.execute(
                """
                SELECT id, name, parent_id, is_posting_level
                FROM responsibilities
                ORDER BY name
            """
            )

            responsibilities = cursor.fetchall()
            conn.close()

            # Build tree structure
            tree_widget.clear()
            items_by_id = {}

            # Create root item
            root_item = UIComponents.create_tree_item("Responsibilities", 0)
            tree_widget.addTopLevelItem(root_item)
            items_by_id[0] = root_item

            # Build hierarchy
            for resp_id, name, parent_id, is_posting_level in responsibilities:
                display_name = f"📍 {name}" if is_posting_level else f"📂 {name}"
                item = UIComponents.create_tree_item(
                    display_name, resp_id, is_posting_level
                )

                parent_item = items_by_id.get(parent_id or 0, root_item)
                parent_item.addChild(item)
                items_by_id[resp_id] = item

            # Expand root
            root_item.setExpanded(True)

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                tree_widget.parent(),
                "Error",
                f"Failed to load responsibilities: {str(e)}",
            )
