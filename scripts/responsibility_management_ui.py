"""
Responsibility Management UI

This module has been refactored into modular components for better maintainability.
The main dialog classes are now in the responsibility_management package.

This module provides backward-compatible imports for the UI components.
"""

# Import the modularized UI components
from scripts.responsibility_management import (
    AddResponsibilityDialog,
    ResponsibilityManagementDialog,
)
