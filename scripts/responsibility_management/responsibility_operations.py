"""
Responsibility Operations Module

Contains core CRUD operations for responsibility management.
"""

import datetime
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class ResponsibilityOperations:
    """
    Handles core responsibility CRUD operations.
    """

    @staticmethod
    def add_responsibility(dialog: "QWidget", data: Dict) -> bool:
        """
        Add a new responsibility to the database.

        Args:
            dialog: Parent dialog for error messages
            data: Responsibility data dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        from .validation import ResponsibilityValidator

        # Validate input data
        if not ResponsibilityValidator.validate_responsibility_data(dialog, data):
            return False

        name = data["name"].strip()
        parent_id = data["parent_id"]
        is_posting_level = data["is_posting_level"]
        contacts = data["contacts"]
        inherited_contacts = data["inherited_contacts"]

        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Insert responsibility
            cursor.execute(
                """
                INSERT INTO responsibilities (name, parent_id, is_posting_level, created_date)
                VALUES (?, ?, ?, ?)
            """,
                (
                    name,
                    parent_id,
                    is_posting_level,
                    datetime.datetime.now().isoformat(),
                ),
            )

            responsibility_id = cursor.lastrowid

            # Insert contacts
            for contact in contacts:
                cursor.execute(
                    """
                    INSERT INTO contacts (
                        responsibility_id, names, surname, title, initials,
                        job_title, telephone, email
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        responsibility_id,
                        contact.get("names"),
                        contact.get("surname"),
                        contact.get("title"),
                        contact.get("initials"),
                        contact.get("job_title"),
                        contact.get("telephone"),
                        contact.get("email"),
                    ),
                )

            # Insert inherited contacts
            for contact in inherited_contacts:
                cursor.execute(
                    """
                    INSERT INTO contacts (
                        responsibility_id, names, surname, title, initials,
                        job_title, telephone, email
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        responsibility_id,
                        contact.get("names"),
                        contact.get("surname"),
                        contact.get("title"),
                        contact.get("initials"),
                        contact.get("job_title"),
                        contact.get("telephone"),
                        contact.get("email"),
                    ),
                )

            conn.commit()
            conn.close()

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "RESPONSIBILITY_ADDED",
                f"Added responsibility '{name}' with {len(contacts)} contacts",
                responsibility_id,
            )

            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                dialog,
                "Success",
                f"Responsibility '{name}' has been added successfully.",
            )

            return True

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                dialog, "Database Error", f"Failed to add responsibility: {str(e)}"
            )
            return False

    @staticmethod
    def edit_responsibility(dialog: "QWidget") -> bool:
        """
        Edit an existing responsibility.

        Args:
            dialog: Parent dialog containing responsibility data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get data from dialog
            resp_id = dialog.resp_id
            name = dialog.name_edit.text().strip()
            is_posting_level = dialog.posting_level_checkbox.isChecked()

            # Get contacts from table
            contacts = []
            for row in range(dialog.contacts_table.rowCount()):
                contact_data = {
                    "names": (
                        dialog.contacts_table.item(row, 0).text()
                        if dialog.contacts_table.item(row, 0)
                        else ""
                    ),
                    "surname": (
                        dialog.contacts_table.item(row, 1).text()
                        if dialog.contacts_table.item(row, 1)
                        else ""
                    ),
                    "title": (
                        dialog.contacts_table.item(row, 2).text()
                        if dialog.contacts_table.item(row, 2)
                        else ""
                    ),
                    "initials": (
                        dialog.contacts_table.item(row, 3).text()
                        if dialog.contacts_table.item(row, 3)
                        else ""
                    ),
                    "job_title": (
                        dialog.contacts_table.item(row, 4).text()
                        if dialog.contacts_table.item(row, 4)
                        else ""
                    ),
                    "telephone": (
                        dialog.contacts_table.item(row, 5).text()
                        if dialog.contacts_table.item(row, 5)
                        else ""
                    ),
                    "email": (
                        dialog.contacts_table.item(row, 6).text()
                        if dialog.contacts_table.item(row, 6)
                        else ""
                    ),
                }
                if any(contact_data.values()):  # Only add if not empty
                    contacts.append(contact_data)

            # Validation
            if not name:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(dialog, "Invalid Input", "Name cannot be empty.")
                return False

            if is_posting_level and not contacts:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    "Posting level responsibilities require at least one contact.",
                )
                return False

            # Update database
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Update responsibility
            cursor.execute(
                """
                UPDATE responsibilities
                SET name = ?, is_posting_level = ?, updated_date = ?
                WHERE id = ?
            """,
                (name, is_posting_level, datetime.datetime.now().isoformat(), resp_id),
            )

            # Delete existing contacts
            cursor.execute(
                "DELETE FROM contacts WHERE responsibility_id = ?", (resp_id,)
            )

            # Insert updated contacts
            for contact in contacts:
                cursor.execute(
                    """
                    INSERT INTO contacts (
                        responsibility_id, names, surname, title, initials,
                        job_title, telephone, email
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        resp_id,
                        contact.get("names"),
                        contact.get("surname"),
                        contact.get("title"),
                        contact.get("initials"),
                        contact.get("job_title"),
                        contact.get("telephone"),
                        contact.get("email"),
                    ),
                )

            conn.commit()
            conn.close()

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "RESPONSIBILITY_EDITED",
                f"Edited responsibility '{name}'",
                resp_id,
            )

            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                dialog,
                "Success",
                f"Responsibility '{name}' has been updated successfully.",
            )

            return True

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                dialog, "Database Error", f"Failed to edit responsibility: {str(e)}"
            )
            return False

    @staticmethod
    def edit_responsibility_by_name(
        parent_dialog: "QWidget", responsibility_name: str
    ) -> bool:
        """
        Edit a responsibility by name (used for testing/mocking).

        Args:
            parent_dialog: Parent dialog
            responsibility_name: Name of responsibility to edit

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Find responsibility by name
            cursor.execute(
                "SELECT id FROM responsibilities WHERE name = ?", (responsibility_name,)
            )
            result = cursor.fetchone()

            if not result:
                conn.close()
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    parent_dialog,
                    "Not Found",
                    f"Responsibility '{responsibility_name}' not found.",
                )
                return False

            resp_id = result[0]
            conn.close()

            # Create mock dialog for editing
            from .mock_classes import MockDialog

            mock_item = {"id": resp_id, "text": responsibility_name}
            edit_dialog = MockDialog(parent_dialog, resp_id, mock_item)

            # Simulate editing
            edit_dialog.refresh_tree()
            edit_dialog.clear_form()
            edit_dialog.accept()

            return edit_dialog.saved

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                parent_dialog, "Error", f"Failed to edit responsibility: {str(e)}"
            )
            return False

    @staticmethod
    def delete_responsibility(dialog: "QWidget") -> bool:
        """
        Delete a responsibility from the database.

        Args:
            dialog: Parent dialog containing tree widget

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get selected responsibility
            current_item = dialog.tree.currentItem()
            if not current_item:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    dialog, "No Selection", "Please select a responsibility to delete."
                )
                return False

            resp_id = getattr(current_item, "resp_id", None)
            if not resp_id:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    dialog,
                    "Invalid Selection",
                    "Selected item is not a valid responsibility.",
                )
                return False

            # Check if responsibility has children
            from scripts.Utilities.tree_utils import get_subtree_resp_ids

            subtree_ids = get_subtree_resp_ids(resp_id)
            if len(subtree_ids) > 1:  # More than just itself
                from PyQt5.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    dialog,
                    "Confirm Deletion",
                    f"This responsibility has {len(subtree_ids)-1} child responsibilities. "
                    "Deleting it will also delete all children and their contacts.\n\n"
                    "This action cannot be undone. Are you sure?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return False

            # Confirm deletion
            from PyQt5.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                dialog,
                "Confirm Deletion",
                "Are you sure you want to delete this responsibility?\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return False

            # Delete from database
            import sqlite3

            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Delete contacts first
            cursor.execute(
                "DELETE FROM contacts WHERE responsibility_id IN ({})".format(
                    ",".join("?" * len(subtree_ids))
                ),
                subtree_ids,
            )

            # Delete responsibilities
            cursor.execute(
                "DELETE FROM responsibilities WHERE id IN ({})".format(
                    ",".join("?" * len(subtree_ids))
                ),
                subtree_ids,
            )

            conn.commit()
            conn.close()

            # Log the action
            from scripts.Utilities.audit_utils import save_audit_log

            save_audit_log(
                "RESPONSIBILITY_DELETED",
                f"Deleted responsibility and {len(subtree_ids)-1} children",
                resp_id,
            )

            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(
                dialog, "Success", "Responsibility has been deleted successfully."
            )

            return True

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                dialog, "Database Error", f"Failed to delete responsibility: {str(e)}"
            )
            return False
