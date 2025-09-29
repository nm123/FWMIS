"""
Application Imports Module

Centralized location for all imports used by the main FWMIS application.
This helps reduce the size of the main application file and improves maintainability.
"""

import os
import sqlite3
import sys
from datetime import datetime

# Qt Graphics/Platform Configuration for crash prevention
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_OPENGL"] = (
    "software"  # Force software rendering to avoid graphics driver issues
)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"  # Disable auto scaling
os.environ["QT_SCALE_FACTOR"] = "1"  # Fixed scale factor
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # Disable high DPI scaling
os.environ["QT_LOGGING_RULES"] = "qt.qpa.plugin=false"  # Reduce plugin logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import PyQt5 modules
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

# Set Qt attributes BEFORE creating QApplication
QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # Force software OpenGL
QApplication.setAttribute(
    Qt.AA_DontCreateNativeWidgetSiblings, True
)  # Prevent native widget issues
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, False)  # Disable high DPI pixmaps


# Import FWMIS modules - using dynamic imports to handle path issues
def _import_fwmis_modules():
    """Import FWMIS modules with proper path handling."""
    import os
    import sys

    # Add the scripts directory to path if not already there
    scripts_dir = os.path.dirname(os.path.dirname(__file__))
    parent_dir = os.path.dirname(scripts_dir)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Import modules using direct imports since we're in the scripts directory
    from case_management import (
        AddNewCaseDialog,
        EditCasesDialog,
        ToDoListDialog,
        ViewCasesDialog,
        ViewDeletedCasesDialog,
    )
    from case_management_modules.write_off_management_dialog import (
        WriteOffManagementDialog,
    )
    from case_management_modules.write_off_submission_dialog import (
        WriteOffSubmissionDialog,
    )
    from category_management import ManageCategoriesDialog
    from email_template_management import ManageEmailTemplatesDialog
    from financial_year_management import FinancialYearManagementDialog
    from list_management import ManageListsDialog
    from optimization_management import open_optimization_management
    from report_management import ReportManagementDialog
    from responsibility_management_ui import ResponsibilityManagementDialog
    from ui.dialogs.admin.delegation_manager import DelegationManagerDialog
    from ui.dialogs.annexure_preparation_dialog import AnnexurePreparationDialog
    from ui.dialogs.checklist_dialog import ChecklistDialog
    from ui.dialogs.import_cases_dialog import import_undisclosed_cases
    from ui.dialogs.import_cases_dialog_core import ImportUndisclosedCasesDialog
    from Utilities.config import DB_PATH, initialize_shared_documents_table
    from Utilities.financial_utils import get_active_period_display
    from Utilities.logging_utils import configure_logging
    from Utilities.qt_diagnostics import (
        apply_qt_fixes,
        check_qt_compatibility,
        print_qt_diagnostics,
    )
    from Utilities.ui_theme import apply_theme, create_status_label
    from wipe_cases_dialog import WipeCasesDialog

    # Make imports available globally in this module
    globals().update(locals())


# Execute the imports
_import_fwmis_modules()
