"""
Responsibility Management Package

This package contains modularized components for responsibility management,
organized by functionality for better maintainability and readability.
"""

# Operations
from .operations import (
    add_responsibility,
    edit_responsibility,
    edit_responsibility_by_name,
    delete_responsibility,
)
from .responsibility_operations import ResponsibilityOperations
from .validation import ResponsibilityValidator
from .mock_classes import MockDialog, MockTreeWidget, MockTreeWidgetItem

# UI Components
from .ui_components import UIComponents
from .add_responsibility_dialog import AddResponsibilityDialog
from .responsibility_management_dialog import ResponsibilityManagementDialog

__all__ = [
    # Operations
    "add_responsibility",
    "edit_responsibility",
    "edit_responsibility_by_name",
    "delete_responsibility",
    "ResponsibilityOperations",
    "ResponsibilityValidator",
    "MockDialog",
    "MockTreeWidget",
    "MockTreeWidgetItem",
    # UI Components
    "UIComponents",
    "AddResponsibilityDialog",
    "ResponsibilityManagementDialog",
]
