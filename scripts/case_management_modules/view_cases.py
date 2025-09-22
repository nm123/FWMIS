"""
View Cases Module - Orchestrator

This module serves as the main entry point for the View Cases functionality.
It imports and orchestrates the UI, logic, and utility components.
"""

from scripts.case_management_modules.view_cases_logic import ViewCasesLogic
from scripts.ui.components.view_cases_ui import (CaseDetailsDialog,
                                                 ViewCasesDialog)
from scripts.Utilities.view_cases_utils import ViewCasesUtils

# Export the main dialog class for external use
__all__ = ["ViewCasesDialog", "CaseDetailsDialog", "ViewCasesLogic", "ViewCasesUtils"]
