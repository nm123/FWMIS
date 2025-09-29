"""
Operations Module for Responsibility Management

Main interface module that combines all responsibility management operations.
"""

from .mock_classes import MockDialog
from .responsibility_operations import ResponsibilityOperations
from .validation import ResponsibilityValidator


def add_responsibility(dialog, data):
    """
    Add a new responsibility.

    Args:
        dialog: Parent dialog
        data: Responsibility data

    Returns:
        bool: True if successful, False otherwise
    """
    return ResponsibilityOperations.add_responsibility(dialog, data)


def edit_responsibility(dialog):
    """
    Edit an existing responsibility.

    Args:
        dialog: Parent dialog

    Returns:
        bool: True if successful, False otherwise
    """
    return ResponsibilityOperations.edit_responsibility(dialog)


def edit_responsibility_by_name(parent_dialog, responsibility_name):
    """
    Edit a responsibility by name.

    Args:
        parent_dialog: Parent dialog
        responsibility_name: Name of responsibility to edit

    Returns:
        bool: True if successful, False otherwise
    """
    return ResponsibilityOperations.edit_responsibility_by_name(
        parent_dialog, responsibility_name
    )


def delete_responsibility(dialog):
    """
    Delete a responsibility.

    Args:
        dialog: Parent dialog

    Returns:
        bool: True if successful, False otherwise
    """
    return ResponsibilityOperations.delete_responsibility(dialog)
