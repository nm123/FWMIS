"""
FWMIS Main Entry Point

This module has been refactored into modular components for better maintainability.
The main application logic is now in app_modules/app_main.py.
"""

# Import the main application from the modular structure
from app_modules.app_main import FWManagementApp, exception_handler

# Import necessary modules for the main entry point
from PyQt5.QtWidgets import QApplication


def main():
    """Main entry point for the FWMIS application."""
    import sys

    # Set up global exception handler
    sys.excepthook = exception_handler

    # Create and configure Qt diagnostics
    from scripts.Utilities.qt_diagnostics import apply_qt_fixes, check_qt_compatibility

    apply_qt_fixes()
    check_qt_compatibility()

    # Configure structured logging
    from scripts.Utilities.logging_utils import configure_logging

    configure_logging()

    # Initialize metrics and monitoring
    from scripts.Utilities.metrics import StructuredLogger, get_health_checker

    health_checker = get_health_checker()

    # Log application startup
    StructuredLogger.log_application_event(
        "application_startup",
        extra_data={"version": "2.0.0", "environment": "production"},
    )

    # Create the application
    app = QApplication(sys.argv)

    # Create and show the main window
    main_window = FWManagementApp()
    main_window.show()

    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
