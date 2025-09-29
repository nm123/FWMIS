"""
Automated Testing Integration Dialog for FWMIS

This module has been refactored into modular components for better maintainability.
The main AutomatedTestingDialog class is now in the automated_testing package.

Provides a comprehensive UI for running automated tests and CI/CD integration including:
- Test suite execution and monitoring
- Test result analysis and reporting
- CI/CD pipeline configuration
- Automated testing scheduling
- Performance regression detection
"""

# Import the modularized dialog
from .automated_testing import AutomatedTestingDialog


def show_automated_testing_dialog(parent=None):
    """
    Show the automated testing dialog.

    Args:
        parent: Parent widget for the dialog

    Returns:
        int: Dialog exit code
    """
    dialog = AutomatedTestingDialog(parent)
    return dialog.exec_()
