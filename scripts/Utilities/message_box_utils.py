"""
Message Box Utilities for FWMIS

This module provides centralized message box functions for consistent user feedback
across the entire application.
"""

from PyQt5.QtWidgets import QMessageBox, QWidget


def show_info_message(parent: QWidget, title: str, message: str) -> None:
    """
    Show an informational message box.

    Args:
        parent: Parent widget
        title: Message box title
        message: Message to display
    """
    QMessageBox.information(parent, title, message)


def show_warning_message(parent: QWidget, title: str, message: str) -> None:
    """
    Show a warning message box.

    Args:
        parent: Parent widget
        title: Message box title
        message: Message to display
    """
    QMessageBox.warning(parent, title, message)


def show_error_message(parent: QWidget, title: str, message: str) -> None:
    """
    Show an error message box.

    Args:
        parent: Parent widget
        title: Message box title
        message: Message to display
    """
    QMessageBox.critical(parent, title, message)


def show_confirmation_dialog(parent: QWidget, title: str, message: str) -> bool:
    """
    Show a confirmation dialog with Yes/No options.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message

    Returns:
        bool: True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    return reply == QMessageBox.Yes


def show_save_confirmation(parent: QWidget, message: str = "Save changes?") -> bool:
    """
    Show a save confirmation dialog.

    Args:
        parent: Parent widget
        message: Custom confirmation message

    Returns:
        bool: True if user wants to save, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        "Confirm Save",
        message,
        QMessageBox.Save | QMessageBox.Cancel,
        QMessageBox.Save,
    )
    return reply == QMessageBox.Save


def show_delete_confirmation(parent: QWidget, item_type: str = "item") -> bool:
    """
    Show a delete confirmation dialog.

    Args:
        parent: Parent widget
        item_type: Type of item being deleted (for message)

    Returns:
        bool: True if user confirms deletion, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        "Confirm Deletion",
        f"Are you sure you want to delete this {item_type}?\n\nThis action cannot be undone.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes
