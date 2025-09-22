#!/usr/bin/env python3
"""
Test script to verify Edit Cases dialog functionality after Qt fixes
"""

import os
import sys

# Apply Qt fixes before importing PyQt5
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_OPENGL"] = "software"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.plugin=false"

sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from scripts.case_management_modules.edit_cases_dialog import EditCasesDialog


def test_edit_cases_dialog():
    """Test the Edit Cases dialog creation and display"""
    print("Testing Edit Cases dialog...")

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Set stability attributes
        app.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, False)

        print("Creating EditCasesDialog...")
        dialog = EditCasesDialog(None)  # No parent for testing
        print("EditCasesDialog created successfully")

        print("Testing dialog display...")
        dialog.show()
        print("Dialog show() called successfully")

        # Process events to allow dialog to render
        app.processEvents()
        print("Events processed successfully")

        # Test dialog functionality briefly
        print("Testing dialog setup completion...")
        # The setup_ui is called in __init__, so if we get here, it worked

        print("Hiding dialog...")
        dialog.hide()
        print("Dialog hidden successfully")

        print("Cleaning up...")
        dialog.close()
        dialog.deleteLater()

        print("[SUCCESS] Edit Cases dialog test completed successfully!")
        return True

    except Exception as e:
        print(f"[FAIL] Edit Cases dialog test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_edit_cases_dialog()
    sys.exit(0 if success else 1)
