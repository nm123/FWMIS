#!/usr/bin/env python3
"""
FWMIS Main Entry Point

This is the main executable script for the Fruitless and Wasteful Expenditure
Management Information System (FWMIS). It initializes the PyQt5 application,
creates the main window, and starts the event loop.

Usage:
    python FWMIS/scripts/fw_management.py
"""

import sys
import os

# Add the scripts directory to the Python path if running from the FWMIS root
if __name__ == "__main__":
    # Ensure we're running from the correct directory structure
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    fwmis_root = os.path.dirname(scripts_dir)
    if fwmis_root not in sys.path:
        sys.path.insert(0, fwmis_root)

from PyQt5.QtWidgets import QApplication
from scripts.app_modules.app_main import FWManagementApp, exception_handler

from scripts.Utilities.metrics_collectors import StructuredLogger

# Set up global exception handler
sys.excepthook = exception_handler


def main():
    """Main function to create and run the FWMIS application."""
    # Create the application
    app = QApplication(sys.argv)

    # Set application name and organization for better integration
    app.setApplicationName("FWMIS")
    app.setOrganizationName("FWMIS Development Team")

    # Create and show the main window
    main_window = FWManagementApp()

    # Log main window creation for monitoring
    StructuredLogger.log_application_event(
        "main_window_created",
        extra_data={"version": "2.0.0", "environment": "production"}
    )

    main_window.show()

    # Log main window display for monitoring
    StructuredLogger.log_application_event(
        "main_window_shown",
        extra_data={"version": "2.0.0", "environment": "production"}
    )

    # Log event loop start for monitoring
    StructuredLogger.log_application_event(
        "event_loop_started",
        extra_data={"version": "2.0.0", "environment": "production"}
    )

    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
