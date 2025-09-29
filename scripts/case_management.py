# Case Management Module
# This module provides access to all case management dialogs and functionality

try:
    # Try relative imports first (when used as part of a package)
    from scripts.ui.dialogs.edit_case import EditCaseDialog

    from .case_management_modules.add_case import AddNewCaseDialog, AssessmentDialog
    from .case_management_modules.deleted_cases import ViewDeletedCasesDialog
    from .case_management_modules.edit_cases_dialog import EditCasesDialog
    from .case_management_modules.responsibility_selection import (
        ResponsibilitySelectionDialog,
    )
    from .case_management_modules.todo_list import ToDoListDialog
    from .case_management_modules.view_cases import CaseDetailsDialog, ViewCasesDialog
    from .ui.dialogs.import_cases_dialog import import_undisclosed_cases

    # Import from new modular structure
    from .ui.dialogs.import_cases_dialog_core import ImportUndisclosedCasesDialog
except ImportError:
    # Fall back to absolute imports (when run directly)
    from scripts.case_management_modules.add_case import (
        AddNewCaseDialog,
        AssessmentDialog,
    )
    from scripts.case_management_modules.deleted_cases import ViewDeletedCasesDialog
    from scripts.case_management_modules.edit_cases_dialog import EditCasesDialog
    from scripts.case_management_modules.responsibility_selection import (
        ResponsibilitySelectionDialog,
    )
    from scripts.case_management_modules.todo_list import ToDoListDialog
    from scripts.case_management_modules.view_cases import (
        CaseDetailsDialog,
        ViewCasesDialog,
    )
    from scripts.ui.dialogs.edit_case import EditCaseDialog
    from scripts.ui.dialogs.import_cases_dialog import import_undisclosed_cases

    # Import from new modular structure
    from scripts.ui.dialogs.import_cases_dialog_core import ImportUndisclosedCasesDialog

# Make all dialogs available at the package level
__all__ = [
    "ResponsibilitySelectionDialog",
    "AddNewCaseDialog",
    "AssessmentDialog",
    "ViewCasesDialog",
    "CaseDetailsDialog",
    "EditCaseDialog",
    "EditCasesDialog",
    "ViewDeletedCasesDialog",
    "ToDoListDialog",
    "ImportUndisclosedCasesDialog",
    "import_undisclosed_cases",
]
