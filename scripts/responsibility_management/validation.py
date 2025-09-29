"""
Validation Module for Responsibility Management

Contains validation logic for responsibility and contact data.
"""

import re
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class ResponsibilityValidator:
    """
    Validates responsibility and contact data.
    """

    @staticmethod
    def validate_responsibility_data(dialog: "QWidget", data: Dict) -> bool:
        """
        Validate responsibility data.

        Args:
            dialog: Parent dialog for error messages
            data: Responsibility data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        from PyQt5.QtWidgets import QMessageBox

        name = data["name"].strip()
        parent_id = data["parent_id"]
        is_posting_level = data["is_posting_level"]
        contacts = data["contacts"]
        inherited_contacts = data["inherited_contacts"]

        # Log input data
        print(
            f"add_responsibility input: name='{name}', parent_id={parent_id}, is_posting_level={is_posting_level}, contacts={contacts}, inherited_contacts={inherited_contacts}"
        )

        # Basic validation
        if not name:
            QMessageBox.warning(dialog, "Invalid Input", "Name cannot be empty.")
            return False

        if len(name) > 100:
            QMessageBox.warning(
                dialog, "Invalid Input", "Name cannot exceed 100 characters."
            )
            return False

        if is_posting_level and not contacts:
            QMessageBox.warning(
                dialog,
                "Invalid Input",
                "Posting level responsibilities require at least one contact.",
            )
            return False

        # Validate contacts
        return ResponsibilityValidator._validate_contacts(dialog, contacts)

    @staticmethod
    def _validate_contacts(dialog: "QWidget", contacts: List[Dict]) -> bool:
        """
        Validate contact data.

        Args:
            dialog: Parent dialog for error messages
            contacts: List of contact dictionaries

        Returns:
            bool: True if all contacts are valid, False otherwise
        """
        from PyQt5.QtWidgets import QMessageBox

        from scripts.Utilities.validation_utils import is_valid_email

        for contact in contacts:
            # Require at least names or surname
            if not (contact.get("names") or contact.get("surname")):
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    "Contact must have at least a name or surname.",
                )
                return False

            # Validate field lengths
            if contact.get("names") and len(contact["names"]) > 100:
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Contact names '{contact['names']}' cannot exceed 100 characters.",
                )
                return False

            if contact.get("surname") and len(contact["surname"]) > 100:
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Contact surname '{contact['surname']}' cannot exceed 100 characters.",
                )
                return False

            if contact.get("title") and len(contact["title"]) > 100:
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Contact title '{contact['title']}' cannot exceed 100 characters.",
                )
                return False

            if contact.get("initials") and len(contact["initials"]) > 10:
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Contact initials '{contact['initials']}' cannot exceed 10 characters.",
                )
                return False

            if contact.get("job_title") and len(contact["job_title"]) > 100:
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Contact job title '{contact['job_title']}' cannot exceed 100 characters.",
                )
                return False

            # Validate telephone format
            if contact.get("telephone") and not re.match(
                r"^[\+]?[(]?[0-9]{1,4}[)]?[-0-9\s]*$", contact["telephone"]
            ):
                QMessageBox.warning(
                    dialog,
                    "Invalid Input",
                    f"Invalid telephone format: {contact['telephone']}",
                )
                return False

            # Validate email format
            if contact.get("email") and not is_valid_email(contact["email"]):
                QMessageBox.warning(
                    dialog, "Invalid Input", f"Invalid email format: {contact['email']}"
                )
                return False

        return True
